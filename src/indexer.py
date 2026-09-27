from parser import parser
from stemmer import stem

documents = {
    "D1": "Python programming is fun and useful.",
    "D2": "I love programming in Python because it is simple.",
    "D3": "Python is powerful for web programming.",
    "D4": "Machine learning and artificial intelligence are changing technology.",
    "D5": "Artificial systems can be intelligent without using machine learning.",
    "D6": "Python programming Python programming is everywhere."
}

def index(documents):
    inverted_index = {}
    document_length = {}
    document_frequency = {}
    total_documents = len(documents)
    
    for doc_id, content in documents.items():
        words = parser(content)
        words = stem(words)
        document_length[doc_id] = len(words)
        for position, word in enumerate(words):
            if word not in inverted_index:
                inverted_index[word] = {}
                document_frequency[word] = 0
            if doc_id not in inverted_index[word]:
                inverted_index[word][doc_id] = {"tf": 0}
                inverted_index[word][doc_id]["positions"] = []
                document_frequency[word] += 1
            inverted_index[word][doc_id]["tf"] += 1
            inverted_index[word][doc_id]["positions"].append(position)
            
    avg_document_length = sum(document_length.values()) / len(document_length)
    search_index = {
        "inverted_index": inverted_index,
        "document_length": document_length,
        "document_frequency": document_frequency,
        "avg_document_length": avg_document_length,
        "total_documents": total_documents
    }
    return search_index