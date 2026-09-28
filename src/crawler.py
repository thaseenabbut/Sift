import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from parser import parser
from stemmer import stem

def crawl(seed_urls, max_pages=100):
    if isinstance(seed_urls, str):
        seed_urls = [seed_urls]

    allowed_domains = {
        urlparse(url).netloc for url in seed_urls
    }
    queue = deque(seed_urls)
    visited = set(seed_urls)
    pages = {}
    while queue and len(pages) < max_pages:
        current_url = queue.popleft()
        try:
            response = requests.get(current_url, timeout=5)
        except requests.RequestException:
            continue
        if response.status_code == 200:
            pages[current_url] = response.text
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(current_url, href)
                parsed_url = urlparse(full_url)
                if full_url not in visited and parsed_url.netloc in allowed_domains:
                    visited.add(full_url)
                    queue.append(full_url)
    return pages

pages = crawl("https://en.wikipedia.org/wiki/Web_crawler", max_pages=100)

print("Pages crawled:", len(pages))

for url, html in pages.items():
    stemmed_tokens = stem(parser(html))
    print(url)
    print(stemmed_tokens[:20])