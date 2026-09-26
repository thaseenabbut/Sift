import math

documents = {
    "D1": "python python programming",
    "D2": "python web programming",
    "D3": "javascript programming"
}

bm25_parameters = {
    "k1": 1.2,
    "b": 0.75
}

def index(documents):
    inverted_index = {}
    document_length = {}
    document_frequency = {}
    total_documents = len(documents)
    for doc_id, content in documents.items():
        words = content.split()
        document_length[doc_id] = len(words)
        for word in words:
            if word not in inverted_index:
                inverted_index[word] = {}
                document_frequency[word] = 0
            if doc_id not in inverted_index[word]:
                inverted_index[word][doc_id] = {"tf": 0}
                document_frequency[word] += 1
            inverted_index[word][doc_id]["tf"] += 1
    avg_document_length = sum(document_length.values()) / len(document_length)
    search_index = {
        "inverted_index": inverted_index,
        "document_length": document_length,
        "document_frequency": document_frequency,
        "avg_document_length": avg_document_length,
        "total_documents": total_documents
    }
    return search_index

def retrieve(query, search_index):
    query_words = query.split()
    relevant_docs = set()
    for word in query_words:
        if word in search_index["inverted_index"]:
            relevant_docs.update(search_index["inverted_index"][word].keys())
    return relevant_docs

def calculate_idf(term, search_index):
    df = search_index["document_frequency"].get(term, 0)
    n = search_index["total_documents"]
    idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
    return idf

def calculate_bm25(term, document_id, search_index, bm25_parameters):
    tf = search_index["inverted_index"][term][document_id]["tf"]
    idf = calculate_idf(term, search_index)
    k1 = bm25_parameters["k1"]
    b = bm25_parameters["b"]
    dl = search_index["document_length"][document_id]
    avg_dl = search_index["avg_document_length"]
    numerator = tf * (k1 + 1)
    denominator = tf + k1 * (1 - b + b * dl / avg_dl)
    return idf * (numerator / denominator)

def score_document(query_terms, document_id, search_index, bm25_parameters):
    score = 0.0
    for term in query_terms:
        if term in search_index["inverted_index"] and document_id in search_index["inverted_index"][term]:
            score += calculate_bm25(term, document_id, search_index, bm25_parameters)
    return score

def search(query, search_index, bm25_parameters):
    relevant_docs = retrieve(query, search_index)
    scored_docs = []
    for doc_id in relevant_docs:
        score = score_document(query.split(), doc_id, search_index, bm25_parameters)
        scored_docs.append((doc_id, score))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return scored_docs

print(search("python programming", index(documents), bm25_parameters))