from datetime import datetime, timezone

import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from document_parser import parser
from indexer import index_page
from schemas.search_index import IndexStats
from schemas.page import Page

def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_path = parsed_url.path.rstrip('/')

    return (
        f"{parsed_url.scheme}://{parsed_url.netloc}"
        f"{normalized_path}"
        f"{'?' + parsed_url.query if parsed_url.query else ''}"
    )

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

    existing = await Page.find_one(Page.url == url)

    if existing is not None:
        if not refresh_existing:
            return False

        existing.title = parsed.title
        existing.meta_description = parsed.meta_description
        existing.clean_text = parsed.clean_text
        existing.h1_headers = parsed.h1_headers
        existing.last_crawled_at = datetime.now(timezone.utc)

        await existing.save()
        await index_page(existing)
        return True

    await parsed.insert()
    await index_page(parsed)
    return True

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
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
               }
            response = requests.get(current_url, headers=headers, timeout=5)
        except requests.RequestException:
            continue
        if response.status_code == 200:
            stored = await persist_crawled_page(
                current_url, response.text, refresh_existing
            )
            if not stored:
                continue
            pages_crawled += 1
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
