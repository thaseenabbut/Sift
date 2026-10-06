import math

bm25_parameters = {
    "k1": 1.2,
    "b": 0.75
}

def calculate_idf(term, search_index):
    df = search_index.document_frequency.get(term, 0)
    n = search_index.total_documents
    idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
    return idf

def calculate_bm25(term, document_id, search_index, bm25_parameters):
    tf = search_index.inverted_index[term].postings[document_id].tf
    idf = calculate_idf(term, search_index)
    k1 = bm25_parameters["k1"]
    b = bm25_parameters["b"]
    dl = search_index.document_length[document_id]
    avg_dl = search_index.avg_document_length
    numerator = tf * (k1 + 1)
    denominator = tf + k1 * (1 - b + b * dl / avg_dl)
    return idf * (numerator / denominator)

async def score_document(query_terms, document_id, search_index, bm25_parameters):
    score = 0.0
    for term in query_terms:
        stemmed_term = term.stemmed
        if stemmed_term in search_index.inverted_index and document_id in search_index.inverted_index[stemmed_term].postings:
            score += calculate_bm25(stemmed_term, document_id, search_index, bm25_parameters)
    return score