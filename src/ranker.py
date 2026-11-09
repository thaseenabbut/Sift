import math

bm25_parameters = {
    "k1": 1.2,
    "b": 0.75
}

proximity_weight = 2.0

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


def calculate_proximity_bonus(term_positions):
    if not term_positions or len(term_positions) < 2:
        return 0.0

    if any(not positions for positions in term_positions):
        return 0.0

    all_positions = sorted(
        (position, term_index)
        for term_index, positions in enumerate(term_positions)
        for position in positions
    )

    left = 0
    term_counts = {}
    terms_covered = 0
    min_window = float("inf")

    for right in range(len(all_positions)):
        position, term_index = all_positions[right]

        term_counts[term_index] = term_counts.get(term_index, 0) + 1

        if term_counts[term_index] == 1:
            terms_covered += 1

        while terms_covered == len(term_positions):
            window_size = (
                all_positions[right][0] - all_positions[left][0] + 1
            )
            min_window = min(min_window, window_size)

            left_term = all_positions[left][1]
            term_counts[left_term] -= 1

            if term_counts[left_term] == 0:
                terms_covered -= 1

            left += 1

    if min_window == float("inf"):
        return 0.0

    return proximity_weight / min_window


def score_document(query_terms, document_id, term_lookup, stats, bm25_parameters, idf_cache):
    bm25_score = 0.0
    term_positions = []
    seen_terms = set()
    
    for term in query_terms:
        stemmed_term = term.stemmed
        
        if stemmed_term in seen_terms:
            continue
        seen_terms.add(stemmed_term)
        
        if stemmed_term not in term_lookup:
            term_positions.append([])
            continue
        
        positions = term_lookup[stemmed_term].postings_by_url.get(document_id, None)
        
        if not positions:
            term_positions.append([])
            continue
            
        bm25_score += calculate_bm25(
            stemmed_term,
            document_id,
            term_lookup,
            stats,
            bm25_parameters,
            idf_cache[stemmed_term],
        )
        
        term_positions.append(positions.positions)
            
    proximity_bonus = calculate_proximity_bonus(term_positions)
    
    final_score = bm25_score + proximity_bonus
    
    return final_score
