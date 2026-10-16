from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib.parse import unquote_plus, urljoin, urlsplit, urlunsplit
import urllib.robotparser
from urllib3.util import retry
from bs4 import BeautifulSoup
from collections import deque
from rich import print

from document_parser import parser, calculate_content_hash
from indexer import (
    ensure_stats,
    index_page,
    migrate_page_url,
    remove_document_from_index,
)

from schemas.search_index import IndexStats
from schemas.page import Page

ROBOTS_USER_AGENT = "SiftBot"

ROBOTS_CACHE = {}
PERMANENT_REDIRECT_STATUS_CODES = {301, 308}
REMOVABLE_HTTP_STATUS_CODES = {404, 410}
RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
TRACKING_QUERY_PARAMETER_PREFIXES = ("utm_",)
TRACKING_QUERY_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def _is_tracking_query_parameter(part):
    key = unquote_plus(part.partition("=")[0]).lower()
    return key.startswith(TRACKING_QUERY_PARAMETER_PREFIXES) or key in TRACKING_QUERY_PARAMETERS


def normalize_url(url):
    if not isinstance(url, str) or not url or url != url.strip() or any(char.isspace() for char in url):
        return None

    try:
        parsed_url = urlsplit(url)
        scheme = parsed_url.scheme.lower()
        if scheme not in {"http", "https"} or not parsed_url.hostname:
            return None
        if parsed_url.username is not None or parsed_url.password is not None:
            return None
        port = parsed_url.port
    except ValueError:
        return None

    hostname = parsed_url.hostname.lower()
    try:
        if ":" not in hostname: 
            hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    if ":" in hostname:
        hostname = f"[{hostname}]"
    if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
        hostname = f"{hostname}:{port}"

    path = parsed_url.path or "/"
    query_parts = [
        part for part in parsed_url.query.split("&")
        if not _is_tracking_query_parameter(part)
    ]
    query = "&".join(query_parts)
    return urlunsplit((scheme, hostname, path, query, ""))


def canonical_url_from_html(html, page_url, allowed_domains):
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for tag in soup.find_all("link"):
        rel = tag.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()
        if "canonical" not in {value.lower() for value in rel}:
            continue
        href = tag.get("href")
        if not href:
            continue
        candidate = normalize_url(urljoin(page_url, href))
        if candidate is not None:
            candidates.append(candidate)

    distinct = set(candidates)
    if len(distinct) != 1:
        return None
    canonical_url = distinct.pop()
    page_parts = urlsplit(page_url)
    canonical_parts = urlsplit(canonical_url)
    if canonical_parts.hostname != page_parts.hostname:
        return None
    if canonical_parts.netloc not in allowed_domains:
        return None
    return canonical_url
    
def allowed_to_fetch(url):
    parsed_url = urlsplit(url)
    origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    if origin not in ROBOTS_CACHE:
        robots_url = f"{origin}/robots.txt"

        try:
            response = requests.get(
                robots_url,
                headers={"User-Agent": ROBOTS_USER_AGENT},
                timeout=5,
            )
        except requests.RequestException:
            ROBOTS_CACHE[origin] = None
            return False

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)

        if response.status_code == 200:
            rp.parse(response.text.splitlines())
        elif 400 <= response.status_code < 500:
            rp.parse([])
        else:
            ROBOTS_CACHE[origin] = None
            return False
        ROBOTS_CACHE[origin] = rp

    rp = ROBOTS_CACHE[origin]

    if rp is None:
        return False

    return rp.can_fetch(ROBOTS_USER_AGENT, url)

async def already_indexed_urls():
    indexed = set()
    stats = await IndexStats.find_one({"id_name": "global_stats"})
    if stats and stats.document_length:
        indexed.update(stats.document_length.keys())
    pages = await Page.find_all().to_list()
    indexed.update(page.url for page in pages)
    # Legacy records may predate the normalization policy. Treat their
    # normalized spellings as seen so a refresh does not create a duplicate.
    indexed.update(
        normalized for url in tuple(indexed)
        if (normalized := normalize_url(url)) is not None
    )
    return indexed


async def persist_crawled_page(url, html, refresh_existing):
    url = normalize_url(url)
    if url is None:
        return False
    parsed = parser(url, html)
    new_hash = calculate_content_hash(parsed.clean_text)
    parsed.content_hash = new_hash

    existing = await Page.find_one({"url": url})

    if existing is not None:
        
        if existing.content_hash == new_hash:
            # A failed prior migration can leave a valid Page without its
            # index entry. Repair it on the next crawl instead of silently
            # treating it as complete.
            stats = await ensure_stats()
            if url not in stats.document_length:
                await index_page(existing)
                return True
            return False

        if not refresh_existing:
            return False

        existing.title = parsed.title
        existing.meta_description = parsed.meta_description
        existing.clean_text = parsed.clean_text
        existing.h1_headers = parsed.h1_headers
        existing.content_hash = new_hash
        existing.last_crawled_at = datetime.now(timezone.utc)

        await existing.save()
        await index_page(existing)
        return True

    await parsed.insert()
    await index_page(parsed)
    return True


def is_permanent_redirect(response, requested_url, final_url):
    # This shi true only when the URL we requested received a 301 or 308 response.
    history = getattr(response, "history", ()) or ()
    return (
        requested_url != final_url
        and bool(history)
        and history[0].status_code in PERMANENT_REDIRECT_STATUS_CODES
    )


async def persist_permanent_redirect(source_url, destination_url, html):
    source_url = normalize_url(source_url)
    destination_url = normalize_url(destination_url)
    if source_url is None or destination_url is None:
        return False
    parsed = parser(destination_url, html)
    new_hash = calculate_content_hash(parsed.clean_text)
    parsed.content_hash = new_hash

    source = await Page.find_one({"url": source_url})
    destination = await Page.find_one({"url": destination_url})

    if destination is not None:
        if source is not None and source_url != destination_url:
            await remove_document_from_index(source_url, delete_page=True)
        stats = await ensure_stats()
        if destination_url not in stats.document_length:
            await index_page(destination)
        return source is not None

    if source is None:
        # when there is nothing to migrate; index the canonical URL directly.
        await parsed.insert()
        await index_page(parsed)
        return True

    if source.content_hash == new_hash:
        migrated = await migrate_page_url(source_url, destination_url, new_hash)
        if migrated:
            return True

    await remove_document_from_index(source_url)
    source.url = destination_url
    source.title = parsed.title
    source.meta_description = parsed.meta_description
    source.clean_text = parsed.clean_text
    source.h1_headers = parsed.h1_headers
    source.content_hash = new_hash
    source.last_crawled_at = datetime.now(timezone.utc)
    await source.save()
    await index_page(source)
    return True


async def reconcile_canonical_alias(requested_url, effective_url, canonical_url):
    """Remove indexed aliases when their safe canonical page already exists.

    A canonical declaration never creates a Page at a URL we have not fetched.
    That avoids writing response content under an unverified target URL.
    """
    target = await Page.find_one({"url": canonical_url})
    if target is None:
        return False

    stats = await ensure_stats()
    if canonical_url not in stats.document_length:
        await index_page(target)

    for alias_url in {requested_url, effective_url} - {canonical_url}:
        await remove_document_from_index(alias_url, delete_page=True)
    return True


async def handle_http_failure(url, status_code):
    url = normalize_url(url)
    if url is None:
        return False
    if status_code not in REMOVABLE_HTTP_STATUS_CODES:
        return False
    return await remove_document_from_index(url, delete_page=True)

def retry_request(url, retries=3):
    headers = {
        "User-Agent": ROBOTS_USER_AGENT
    }

    retry_strategy = retry.Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=sorted(RETRYABLE_HTTP_STATUS_CODES),
        allowed_methods=["GET"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)

    with requests.Session() as session:
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            return session.get(url, headers=headers, timeout=5)
        except requests.TooManyRedirects:
            return None
        except requests.RequestException:
            return None

async def crawl(seed_urls, max_pages=100, refresh_existing=False):
    if isinstance(seed_urls, str):
        seed_urls = [seed_urls]
    seed_urls = [normalized for url in seed_urls if (normalized := normalize_url(url))]
    if not seed_urls:
        return 0

    allowed_domains = {
        urlsplit(url).netloc for url in seed_urls
    }
    
    indexed = await already_indexed_urls()
    visited = set() if refresh_existing else set(indexed)
    queue = deque()
    for url in seed_urls:
        if refresh_existing or url not in indexed:
            visited.add(url)
            queue.append(url)

    if not queue:
        return 0

    pages_crawled = 0
    
    while queue and pages_crawled < max_pages:
        current_url = queue.popleft()
        
        if not allowed_to_fetch(current_url):
            continue

        print(f"\n[bold blue][SiftBot][/bold blue] Crawling: {current_url}")

        response = retry_request(current_url)
        if response is None:
            print(
                f"\n[bold red][SiftBot][/bold red] Failed to crawl: {current_url}. "
                "Existing index data was kept."
            )
            continue

        final_url = normalize_url(response.url)
        if final_url is None:
            print(f"\n[bold yellow][SiftBot][/bold yellow] Skipped malformed final URL: {current_url}")
            continue

        if urlsplit(final_url).netloc not in allowed_domains:
            print(f"\n[bold yellow][SiftBot][/bold yellow] Skipped redirect outside allowed domains: {final_url}")
            continue
        
        if response.status_code != 200:
            removed = await handle_http_failure(current_url, response.status_code)
            outcome = (
                " Removed stale indexed page."
                if removed
                else " Existing index data was kept."
            )
            print(
                f"\n[bold yellow][SiftBot][/bold yellow] Skipped ({response.status_code}): "
                f"{current_url}.{outcome}"
            )  
            continue

        canonical_url = canonical_url_from_html(
            response.text, final_url, allowed_domains
        )
        if canonical_url is not None and canonical_url != final_url:
            if await reconcile_canonical_alias(current_url, final_url, canonical_url):
                print(
                    f"\n[bold blue][SiftBot][/bold blue] Canonical alias resolved: "
                    f"{current_url} -> {canonical_url}"
                )
            elif canonical_url not in visited:
                visited.add(canonical_url)
                queue.append(canonical_url)
                print(
                    f"\n[bold yellow][SiftBot][/bold yellow] Deferred canonical alias "
                    f"until target is crawled: {canonical_url}"
                )
            # Do not index response content at a canonical target that has not
            # been fetched, and do not duplicate an authoritative target.
            continue

        if is_permanent_redirect(response, current_url, final_url):
            stored = await persist_permanent_redirect(
                current_url, final_url, response.text
            )
        else:
            # Preserve the established behaviour for 302/307 responses: their
            # content is associated with the originally requested URL, not
            # silently migrated to response.url.
            stored = await persist_crawled_page(
                current_url, response.text, refresh_existing
            )

        if not stored:
            continue
        
        pages_crawled += 1
        print(f"\n[bold blue][SiftBot][/bold blue] Indexed: {current_url}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(current_url, href)
            normal_url = normalize_url(full_url)
            if normal_url is None:
                continue
            parsed_url = urlsplit(normal_url)
                
            if normal_url not in visited and parsed_url.netloc in allowed_domains:
                visited.add(normal_url)
                queue.append(normal_url)

    return pages_crawled
