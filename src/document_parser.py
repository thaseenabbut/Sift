import hashlib
from bs4 import BeautifulSoup
from schemas.page import Page

def parser(url, html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else "No title"
    description = soup.find("meta", attrs={"name": "description"})
    meta_description = description.get("content", "").strip() if description else None
    h1_headers = [header.get_text(" ", strip=True) for header in soup.find_all("h1")]

    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        element.decompose()

    clean_text = soup.get_text(separator=" ", strip=True)

    return Page(
        url=url,
        title=title,
        meta_description=meta_description,
        h1_headers=h1_headers,
        clean_text=clean_text,
    )

def calculate_content_hash(clean_text):
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
