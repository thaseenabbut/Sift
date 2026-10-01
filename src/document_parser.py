from bs4 import BeautifulSoup

def parser(text):
    soup = BeautifulSoup(text, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "hˀeader", "noscript", "aside"]):
        element.decompose()
    return soup.get_text(separator=" ", strip=True)