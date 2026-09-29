import re
from bs4 import BeautifulSoup

def parser(text):
    soup = BeautifulSoup(text, "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()
    text = soup.get_text(" ")
    text = text.lower()
    text = re.sub(r'-', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    return words