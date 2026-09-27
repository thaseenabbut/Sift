def retrieve(query_terms, search_index):
    relevant_docs = set()
    for word in query_terms:
        if word in search_index["inverted_index"]:
            relevant_docs.update(search_index["inverted_index"][word].keys())
    return relevant_docs

def phrase_search(query_terms, document_id, search_index):
    if not query_terms:
        return False
    if document_id not in search_index["document_length"]:
        return False
        
    for term in query_terms:
        if term not in search_index["inverted_index"] or document_id not in search_index["inverted_index"][term]:
            return False
            
    first_term = query_terms[0]
    candidate_positions = search_index["inverted_index"][first_term][document_id]["positions"]
    
    for i in range(1, len(query_terms)):
        term = query_terms[i]
        term_positions = set(search_index["inverted_index"][term][document_id]["positions"])
        
        candidate_positions = [pos for pos in candidate_positions if (pos + i) in term_positions]
        
        if not candidate_positions:
            return False
            
    return True