from document_parser import parser
from tokenizer import tokenize
from stemmer import stem

def index(pages):
    inverted_index = {}
    document_length = {}
    document_frequency = {}
    total_documents = len(pages)
    if total_documents == 0:
        return {
            "inverted_index": {},
            "document_length": {},
            "document_frequency": {},
            "avg_document_length": 0,
            "total_documents": 0
        }
    
    for url, content in pages.items():
        words = stem(tokenize(parser(content)))
        document_length[url] = len(words)
        for position, word in enumerate(words):
            if word not in inverted_index:
                inverted_index[word] = {}
                document_frequency[word] = 0
            if url not in inverted_index[word]:
                inverted_index[word][url] = {"tf": 0}
                inverted_index[word][url]["positions"] = []
                document_frequency[word] += 1
            inverted_index[word][url]["tf"] += 1
            inverted_index[word][url]["positions"].append(position)
            
    avg_document_length = sum(document_length.values()) / total_documents
    search_index = {
        "inverted_index": inverted_index,
        "document_length": document_length,
        "document_frequency": document_frequency,
        "avg_document_length": avg_document_length,
        "total_documents": total_documents
    }
    
    return search_index