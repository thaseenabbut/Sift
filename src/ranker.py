import math

bm25_parameters = {
    "k1": 1.2,
    "b": 0.75
}

def collect_ranking_terms(parsed):
    unique = []
    seen = set()
    for term in (
        *parsed.terms,
        *parsed.required,
        *parsed.intitle,
        *parsed.inurl,
        *parsed.related,
        *(term for phrase in parsed.phrases for term in phrase),
    ):
        if term.stemmed not in seen:
            seen.add(term.stemmed)
            unique.append(term)
    return unique


def calculate_idf(term, term_lookup, stats):
    df = term_lookup[term].document_frequency
    n = stats.total_documents
    return math.log((n - df + 0.5) / (df + 0.5) + 1)


def build_idf_cache(query_terms, term_lookup, stats):
    return {
        term.stemmed: calculate_idf(term.stemmed, term_lookup, stats)
        for term in query_terms
        if term.stemmed in term_lookup
    }


def calculate_bm25(term, document_id, term_lookup, stats, bm25_parameters, idf):
    tf = term_lookup[term].postings_by_url[document_id].tf
    k1 = bm25_parameters["k1"]
    b = bm25_parameters["b"]
    avg_dl = stats.avg_document_length
    if avg_dl <= 0:
        avg_dl = 1.0
    dl = stats.document_length.get(document_id) or avg_dl
    numerator = tf * (k1 + 1)
    denominator = tf + k1 * (1 - b + b * dl / avg_dl)
    return idf * (numerator / denominator)


def score_document(query_terms, document_id, term_lookup, stats, bm25_parameters, idf_cache):
    score = 0.0
    for term in query_terms:
        stemmed_term = term.stemmed
        if stemmed_term in term_lookup and document_id in term_lookup[stemmed_term].postings_by_url:
            score += calculate_bm25(
                stemmed_term,
                document_id,
                term_lookup,
                stats,
                bm25_parameters,
                idf_cache[stemmed_term],
            )
    return score
