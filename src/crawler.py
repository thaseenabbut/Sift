import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from document_parser import parser

def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_path = parsed_url.path.rstrip('/')
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{normalized_path}{parsed_url.query}"
    
    return normalized_url

def crawl(seed_urls, max_pages=100):
    if isinstance(seed_urls, str):
        seed_urls = [seed_urls]
    seed_urls = [normalize_url(url) for url in seed_urls]

    allowed_domains = {
        urlparse(url).netloc for url in seed_urls
    }
    
    queue = deque(seed_urls)
    visited = set(seed_urls)
    pages = {}
    
    while queue and len(pages) < max_pages:
        current_url = queue.popleft()
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
               }
            response = requests.get(current_url, headers=headers, timeout=5)
        except requests.RequestException:
            continue
        if response.status_code == 200:
            doc = parser(current_url, response.text)
            pages[current_url] = doc
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                full_url = urljoin(current_url, href)
                normal_url = normalize_url(full_url)
                parsed_url = urlparse(normal_url)
                
                if normal_url not in visited and parsed_url.netloc in allowed_domains:
                    visited.add(normal_url)
                    queue.append(normal_url)
    return pages