import re

def parser(text):
    text = text.lower()
    text = re.sub(r'-', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    return words