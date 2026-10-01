from urllib.parse import urlparse

def retrieve(parsed_query, search_index):
    inverted_index = search_index["inverted_index"]
    candidates = set()
    for term in parsed_query["terms"]:
        if term in inverted_index:
            candidates.update(inverted_index[term].keys())
    for phrase_terms in parsed_query["phrases"]:
        for term in phrase_terms:
            if term in inverted_index:
                candidates.update(inverted_index[term].keys())
    for term in parsed_query["intitle"]:
        if term in inverted_index:
            candidates.update(inverted_index[term].keys())
    for term in parsed_query["inurl"]:
        if term in inverted_index:
            candidates.update(inverted_index[term].keys())
    for term in parsed_query["related"]:
        if term in inverted_index:
            candidates.update(inverted_index[term].keys())
    for term in parsed_query["required"]:
        if term in inverted_index:
            candidates &= set(inverted_index[term].keys())
        else:
            return set()
    return candidates


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

def apply_operators(parsed_query, relevant_docs, search_index, pages):
    from bs4 import BeautifulSoup

    filtered = set(relevant_docs)

    for phrase_terms in parsed_query["phrases"]:
        filtered = {
            doc_id for doc_id in filtered
            if phrase_search(phrase_terms, doc_id, search_index)
        }

    for term in parsed_query["excluded"]:
        if term in search_index["inverted_index"]:
            excluded_docs = set(search_index["inverted_index"][term].keys())
            filtered -= excluded_docs

    for term in parsed_query["required"]:
        if term in search_index["inverted_index"]:
            required_docs = set(search_index["inverted_index"][term].keys())
            filtered &= required_docs
        else:
            return set()

    if parsed_query["site_filter"]:
        site = parsed_query["site_filter"].lower()
        filtered = {
            doc_id for doc_id in filtered
            if urlparse(doc_id).netloc.lower().endswith(site)
        }

    if parsed_query["intitle"]:
        def title_contains_terms(doc_id):
            html = pages.get(doc_id, "")
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.lower() if soup.title and soup.title.string else ""
            return all(term in title for term in parsed_query["intitle"])
        
        filtered = {doc_id for doc_id in filtered if title_contains_terms(doc_id)}
        
    if parsed_query["inurl"]:
        def url_contains_terms(doc_id):
            return all(term in doc_id.lower() for term in parsed_query["inurl"])
        
        filtered = {doc_id for doc_id in filtered if url_contains_terms(doc_id)}

    if parsed_query["related"]:
        def related_contains_terms(doc_id):
            return all(term in doc_id.lower() for term in parsed_query["related"])
        
        filtered = {doc_id for doc_id in filtered if related_contains_terms(doc_id)}

    return filtered