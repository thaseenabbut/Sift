import logging
import time
import urllib.robotparser
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import unquote_plus, urljoin, urlsplit, urlunsplit

import requests
import tldextract
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from rich import print
from urllib3.util import retry


def _format_eta(seconds):
    if seconds < 0:
        return "calculating..."
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} seconds"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} minutes {secs} seconds"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} hours {minutes} minutes"
    days, hours = divmod(hours, 24)
    return f"{days} days {hours} hours"

from document_parser import calculate_content_hash, parser
from indexer import (
    ensure_stats,
    migrate_page_url,
    remove_document_from_index,
)
from schemas.page import Page
from schemas.search_index import IndexStats
from src.indexing_pipeline import IndexingResult, PageIndexingPipeline

ROBOTS_USER_AGENT = "SiftBot"
logger = logging.getLogger(__name__)
indexing_pipeline = PageIndexingPipeline()

ROBOTS_CACHE = {}
PERMANENT_REDIRECT_STATUS_CODES = {301, 308}
REMOVABLE_HTTP_STATUS_CODES = {404, 410}
RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
TRACKING_QUERY_PARAMETER_PREFIXES = ("utm_",)
TRACKING_QUERY_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


@dataclass
class PagePersistResult:
    success: bool
    status: str
    indexing: IndexingResult | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.success


@dataclass
class CrawlSummary:
    urls_discovered: int = 0
    pages_successfully_crawled: int = 0
    new_pages: int = 0
    changed_pages: int = 0
    unchanged_pages_skipped: int = 0
    pages_indexed_bm25: int = 0
    pages_processed_chunking: int = 0
    total_chunks_generated: int = 0
    total_embeddings_saved: int = 0
    failed_pages: list[str] = field(default_factory=list)
    indexing_failures: list[str] = field(default_factory=list)

    def record(self, result: PagePersistResult, url: str) -> None:
        if result.status == "new":
            self.new_pages += 1
        elif result.status == "changed":
            self.changed_pages += 1
        elif result.status == "unchanged":
            self.unchanged_pages_skipped += 1

        if result.success:
            self.pages_successfully_crawled += 1
        elif result.status == "failed":
            self.failed_pages.append(url)
            if result.error:
                self.indexing_failures.append(f"{url}: {result.error}")

        indexing = result.indexing
        if indexing is None:
            return
        self.pages_indexed_bm25 += int(indexing.bm25_indexed)
        if not indexing.chunks_skipped:
            self.pages_processed_chunking += 1
        self.total_chunks_generated += indexing.chunks_generated
        self.total_embeddings_saved += indexing.embeddings_saved

    def print_final(self) -> None:
        print("\n[bold green][INDEX SUMMARY][/bold green]")
        print(f"URLs discovered: {self.urls_discovered}")
        print(f"Pages successfully crawled: {self.pages_successfully_crawled}")
        print(f"New pages: {self.new_pages}")
        print(f"Changed pages: {self.changed_pages}")
        print(f"Unchanged pages skipped: {self.unchanged_pages_skipped}")
        print(f"Pages indexed in BM25: {self.pages_indexed_bm25}")
        print(f"Pages processed for chunking: {self.pages_processed_chunking}")
        print(f"Total chunks generated: {self.total_chunks_generated}")
        print(f"Total embeddings saved: {self.total_embeddings_saved}")
        print(f"Failed pages: {len(self.failed_pages)}")
        print(f"Indexing failures: {len(self.indexing_failures)}")


def is_tracking_query_parameter(part):
    key = unquote_plus(part.partition("=")[0]).lower()
    return key.startswith(TRACKING_QUERY_PARAMETER_PREFIXES) or key in TRACKING_QUERY_PARAMETERS

def filter_seed_urls(seed_urls, indexed_urls, refresh_existing=False):
    result = []
    for url in seed_urls:
        normalized = normalize_url(url)
        if normalized is None:
            continue
        if refresh_existing or normalized not in indexed_urls:
            result.append(normalized)
    return result


async def record_alias(alias_url, target_url):
    alias_url = normalize_url(alias_url)
    target_url = normalize_url(target_url)
    if alias_url is None or target_url is None or alias_url == target_url:
        return
    page = await Page.find_one({"url": target_url})
    if page is not None:
        await page.update({"$addToSet": {"aliases": alias_url}})

def normalize_url(url):
    if not isinstance(url, str):
        return None
    
    url = url.strip()
    
    if not url:
        return None
    
    if " " in url:
        return None

    if "://" not in url:
        url = "https://" + url

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
        if not is_tracking_query_parameter(part)
    ]
    query = "&".join(query_parts)
    return urlunsplit((scheme, hostname, path, query, ""))

def get_allowed_scopes(url):
    extracted = tldextract.extract(url)
    return extracted.registered_domain


def is_domain_allowed(hostname, allowed_registered_domains):
    extracted = tldextract.extract(hostname)
    return extracted.registered_domain in allowed_registered_domains


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
    if not is_domain_allowed(canonical_parts.hostname, allowed_domains):
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
    for page in pages:
        indexed.add(page.url)
        indexed.update(page.aliases or [])
    return indexed


async def persist_crawled_page(url, html, refresh_existing):
    url = normalize_url(url)
    if url is None:
        return PagePersistResult(False, "failed", error="Invalid page URL")
    parsed = parser(url, html)
    new_hash = calculate_content_hash(parsed.clean_text)
    parsed.content_hash = new_hash

    existing = await Page.find_one({"url": url})

    if existing is not None:
        if existing.content_hash == new_hash:
            stats = await ensure_stats()
            needs_bm25 = url not in stats.document_length
            needs_chunks = existing.chunk_content_hash != new_hash
            if not needs_bm25 and not needs_chunks:
                return PagePersistResult(False, "unchanged")
            try:
                indexing = await indexing_pipeline.index_page(
                    existing,
                    rebuild_bm25=needs_bm25,
                    rebuild_chunks=needs_chunks,
                )
            except Exception as exc:
                logger.exception("Failed to complete recovery indexing for url=%s", url)
                return PagePersistResult(False, "failed", error=str(exc))
            # The content itself is unchanged; this was a repair of a missing
            # BM25 or vector representation, not a newly crawled document.
            return PagePersistResult(True, "unchanged", indexing)

        if not refresh_existing:
            return PagePersistResult(False, "unchanged")

        existing.title = parsed.title
        existing.meta_description = parsed.meta_description
        existing.clean_text = parsed.clean_text
        existing.h1_headers = parsed.h1_headers
        existing.content_hash = new_hash
        existing.last_crawled_at = datetime.now(UTC)

        await existing.save()
        try:
            indexing = await indexing_pipeline.index_page(
                existing,
                rebuild_bm25=True,
                rebuild_chunks=True,
            )
        except Exception as exc:
            logger.exception("Failed to index changed page url=%s", url)
            return PagePersistResult(False, "failed", error=str(exc))
        return PagePersistResult(True, "changed", indexing)

    await parsed.insert()
    try:
        indexing = await indexing_pipeline.index_page(
            parsed,
            rebuild_bm25=True,
            rebuild_chunks=True,
        )
    except Exception as exc:
        logger.exception("Failed to index new page url=%s", url)
        return PagePersistResult(False, "failed", error=str(exc))
    return PagePersistResult(True, "new", indexing)


def is_permanent_redirect(response, requested_url, final_url):
    # This shi true only when the URL we requested received a 301 or 308 response.
    history = getattr(response, "history", ()) or ()
    return (
        requested_url != final_url
        and bool(history)
        and history[0].status_code in PERMANENT_REDIRECT_STATUS_CODES
    )


async def persist_permanent_redirect(source_url, destination_url, html, refresh_existing=False):
    source_url = normalize_url(source_url)
    destination_url = normalize_url(destination_url)
    if source_url is None or destination_url is None:
        return PagePersistResult(False, "failed", error="Invalid redirect URL")
    parsed = parser(destination_url, html)
    new_hash = calculate_content_hash(parsed.clean_text)
    parsed.content_hash = new_hash

    source = await Page.find_one({"url": source_url})
    destination = await Page.find_one({"url": destination_url})

    if destination is not None:
        if source is not None and source_url != destination_url:
            await remove_document_from_index(source_url, delete_page=True)
        updated = await persist_crawled_page(destination_url, html, refresh_existing)
        if updated or source is None:
            return updated
        return PagePersistResult(True, "unchanged", updated.indexing)

    if source is None:
        # when there is nothing to migrate; index the canonical URL directly.
        await parsed.insert()
        try:
            indexing = await indexing_pipeline.index_page(
                parsed,
                rebuild_bm25=True,
                rebuild_chunks=True,
            )
        except Exception as exc:
            logger.exception("Failed to index redirected page url=%s", destination_url)
            return PagePersistResult(False, "failed", error=str(exc))
        return PagePersistResult(True, "new", indexing)

    if source.content_hash == new_hash:
        migrated = await migrate_page_url(source_url, destination_url, new_hash)
        if migrated:
            return PagePersistResult(True, "changed")

    await remove_document_from_index(source_url)
    source.url = destination_url
    source.title = parsed.title
    source.meta_description = parsed.meta_description
    source.clean_text = parsed.clean_text
    source.h1_headers = parsed.h1_headers
    source.content_hash = new_hash
    source.last_crawled_at = datetime.now(UTC)
    await source.save()
    try:
        indexing = await indexing_pipeline.index_page(
            source,
            rebuild_bm25=True,
            rebuild_chunks=True,
        )
    except Exception as exc:
        logger.exception("Failed to index redirected page url=%s", destination_url)
        return PagePersistResult(False, "failed", error=str(exc))
    return PagePersistResult(True, "changed", indexing)


async def reconcile_canonical_alias(requested_url, effective_url, canonical_url):
    target = await Page.find_one({"url": canonical_url})
    if target is None:
        return False

    stats = await ensure_stats()
    needs_bm25 = canonical_url not in stats.document_length
    needs_chunks = target.chunk_content_hash != target.content_hash
    if needs_bm25 or needs_chunks:
        try:
            await indexing_pipeline.index_page(
                target,
                rebuild_bm25=needs_bm25,
                rebuild_chunks=needs_chunks,
            )
        except Exception:
            logger.exception("Failed to recover canonical target url=%s", canonical_url)
            return False

    for alias_url in {requested_url, effective_url} - {canonical_url}:
        await remove_document_from_index(alias_url, delete_page=True)
        await record_alias(alias_url, canonical_url)
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

async def crawl(seed_urls, max_pages=10000000, refresh_existing=False):
    if isinstance(seed_urls, str):
        seed_urls = [seed_urls]
    seed_urls = [normalized for url in seed_urls if (normalized := normalize_url(url))]
    if not seed_urls:
        print("[bold red][SiftBot][/bold red] No valid seed URLs provided.")
        return 0

    allowed_domains = {
        tldextract.extract(url).registered_domain for url in seed_urls
    }
    
    indexed = await already_indexed_urls()
    visited = set() if refresh_existing else set(indexed)
    queue = deque()
    for url in seed_urls:
        if refresh_existing or url not in indexed:
            visited.add(url)
            queue.append(url)

    if not queue:
        return CrawlSummary()

    summary = CrawlSummary(urls_discovered=len(queue))
    discovered_this_run = set(queue)
    pages_crawled = 0
    urls_processed = 0  # all URLs dequeued (including skips)
    crawl_start_time = time.monotonic()

    while queue and pages_crawled < max_pages:
        current_url = queue.popleft()
        urls_processed += 1
        page_start_time = time.monotonic()

        if not allowed_to_fetch(current_url):
            continue

        # Build progress / ETA status line
        total_known = pages_crawled + len(queue) + 1
        progress = f"{pages_crawled + 1}/{total_known}"
        elapsed_total = time.monotonic() - crawl_start_time
        elapsed_str = _format_eta(elapsed_total)

        if urls_processed > 1 and elapsed_total > 0:
            rate = urls_processed / elapsed_total  # URLs/sec
            remaining_urls = len(queue)
            eta_seconds = remaining_urls / rate
            eta_str = f" | ETA: ~{_format_eta(eta_seconds)}"
        else:
            eta_str = " | ETA: calculating..."

        print(
            f"\n[bold blue][SiftBot][/bold blue] [{progress}] Crawling: {current_url}"
            f" [dim]({elapsed_str}{eta_str})[/dim]"
        )

        response = retry_request(current_url)
        
        if response is not None:
            response.encoding = response.apparent_encoding
            
        if response is None:
            print(
                f"\n[bold red][SiftBot][/bold red] Failed to crawl: {current_url}. "
                "Existing index data was kept."
            )
            summary.failed_pages.append(current_url)
            continue

        final_url = normalize_url(response.url)
        if final_url is None:
            print(f"\n[bold yellow][SiftBot][/bold yellow] Skipped malformed final URL: {current_url}")
            continue

        if not is_domain_allowed(urlsplit(final_url).hostname, allowed_domains):
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
            summary.failed_pages.append(current_url)
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
                discovered_this_run.add(canonical_url)
                summary.urls_discovered = len(discovered_this_run)
                print(
                    f"\n[bold yellow][SiftBot][/bold yellow] Deferred canonical alias "
                    f"until target is crawled: {canonical_url}"
                )
            # Do not index response content at a canonical target that has not
            # been fetched, and do not duplicate an authoritative target.
            continue

        if is_permanent_redirect(response, current_url, final_url):
            stored = await persist_permanent_redirect(
                current_url, final_url, response.text, refresh_existing
            )
            await record_alias(current_url, final_url)
        else:
            # Preserve the established behaviour for 302/307 responses: their
            # content is associated with the originally requested URL, not
            # silently migrated to response.url.
            stored = await persist_crawled_page(
                current_url, response.text, refresh_existing
            )

        summary.record(stored, current_url)
        if not stored:
            continue
        
        pages_crawled += 1
        page_elapsed = time.monotonic() - page_start_time
        print(
            f"\n[bold blue][SiftBot][/bold blue] Indexed: {current_url}"
            f" [dim]({page_elapsed:.1f}s)[/dim]"
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(current_url, href)
            normal_url = normalize_url(full_url)
            if normal_url is None:
                continue
            parsed_url = urlsplit(normal_url)
                
            if normal_url not in visited and is_domain_allowed(parsed_url.hostname, allowed_domains):
                visited.add(normal_url)
                queue.append(normal_url)
                discovered_this_run.add(normal_url)
                summary.urls_discovered = len(discovered_this_run)

    total_elapsed = time.monotonic() - crawl_start_time
    if pages_crawled > 0:
        avg = total_elapsed / pages_crawled
        print(
            f"\n[bold green][SiftBot][/bold green] Crawl complete: {pages_crawled} page(s) in {_format_eta(total_elapsed)} (avg {avg:.1f}s/page)"
        )

    summary.print_final()
    return summary
