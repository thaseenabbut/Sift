from bs4 import BeautifulSoup

class Document:
    def __init__(self, url, title, text):
        self.url = url
        self.title = title
        self.text = text

    def __repr__(self):
        return f"Document(url={self.url!r}, title={self.title!r})"

def parser(url, html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else "No title"

    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return Document(url=url, title=title, text=text)