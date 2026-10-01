import re

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", 
    "in", "into", "is", "it", "no", "not", "of", "on", "or", "such", 
    "that", "the", "their", "then", "there", "these", "they", "this", 
    "to", "was", "will", "with"
}

def tokenize(text):

    text = text.lower()
    text = re.sub(r'[-_]', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = [word for word in text.split() if word not in STOPWORDS]
    
    return words
