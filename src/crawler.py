import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque


def crawl(url, max_pages=100):
    base_domain = urlparse(url).netloc
    queue = deque([url])
    visited = set()
    pages = {}
    while queue:
        current_url = queue.popleft()
        if current_url not in visited and len(pages) < max_pages:
            visited.add(current_url)
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
                    if parsed_url.netloc == base_domain and full_url not in visited:
                        queue.append(full_url)
    return pages