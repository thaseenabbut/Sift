from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urlparse
import urllib.robotparser
from urllib3.util import retry
from bs4 import BeautifulSoup
from collections import deque
from rich import print

from document_parser import parser, calculate_content_hash
from indexer import index_page

from schemas.search_index import IndexStats
from schemas.page import Page

ROBOTS_USER_AGENT = "SiftBot"

ROBOTS_CACHE = {}

def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_path = parsed_url.path.rstrip('/')

    return (
        f"{parsed_url.scheme}://{parsed_url.netloc}"
        f"{normalized_path}"
        f"{'?' + parsed_url.query if parsed_url.query else ''}"
    )
    
def allowed_to_fetch(url):
    parsed_url = urlparse(url)
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
    stats = await IndexStats.find_one(IndexStats.id_name == "global_stats")
    if stats and stats.document_length:
        indexed.update(stats.document_length.keys())
    pages = await Page.find_all().to_list()
    indexed.update(page.url for page in pages)
    return indexed


async def persist_crawled_page(url, html, refresh_existing):
    parsed = parser(url, html)
    new_hash = calculate_content_hash(parsed.clean_text)
    parsed.content_hash = new_hash

    existing = await Page.find_one(Page.url == url)

    if existing is not None:
        
        if existing.content_hash == new_hash:
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

def retry_request(url, retries=3):
    headers = {
        "User-Agent": ROBOTS_USER_AGENT
    }

    retry_strategy = retry.Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)

    with requests.Session() as session:
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            return session.get(url, headers=headers, timeout=5)
        except requests.RequestException:
            return None

async def crawl(seed_urls, max_pages=100, refresh_existing=False):
    if isinstance(seed_urls, str):
        seed_urls = [seed_urls]
    seed_urls = [normalize_url(url) for url in seed_urls]

    allowed_domains = {
        urlparse(url).netloc for url in seed_urls
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

        print(f"[bold blue][SiftBot][/bold blue] Crawling: {current_url}")
        response = retry_request(current_url)

        if response is None:
            print(f"[bold red][SiftBot][/bold red] Failed to crawl: {current_url}")
            continue
        
        if response.status_code != 200:
            print(
                f"[bold yellow][SiftBot][/bold yellow] Skipped ({response.status_code}): "
                f"{current_url}"
            )  
            continue

        stored = await persist_crawled_page(
            current_url, response.text, refresh_existing
        )

        if not stored:
            continue
        
        pages_crawled += 1
        print(f"[bold blue][SiftBot][/bold blue] Indexed: {current_url}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(current_url, href)
            normal_url = normalize_url(full_url)
            parsed_url = urlparse(normal_url)
                
            if normal_url not in visited and parsed_url.netloc in allowed_domains:
                visited.add(normal_url)
                queue.append(normal_url)

    return pages_crawled
