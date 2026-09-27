import nltk

stemmer = nltk.stem.PorterStemmer()

def stem(tokens):
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    return stemmed_tokens