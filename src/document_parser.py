from bs4 import BeautifulSoup
from schemas.page import Page


def parser(url, html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else "No title"

    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        element.decompose()

    clean_text = soup.get_text(separator=" ", strip=True)

    return Page(url=url, title=title, clean_text=clean_text)