from urllib.parse import urlparse

def retrieve(parsed_query, term_docs_lookup):
    candidates = set()
    for term in [term.stemmed for term in parsed_query.terms]:
        if term in term_docs_lookup:
            candidates.update(term_docs_lookup[term].postings.keys())
    for phrase_terms in parsed_query.phrases:
        for term in [term.stemmed for term in phrase_terms]:
            if term in term_docs_lookup:
                candidates.update(term_docs_lookup[term].postings.keys())
    for term in [term.stemmed for term in parsed_query.intitle]:
        if term in term_docs_lookup:
            candidates.update(term_docs_lookup[term].postings.keys())
    for term in [term.stemmed for term in parsed_query.inurl]:
        if term in term_docs_lookup:
            candidates.update(term_docs_lookup[term].postings.keys())
    for term in [term.stemmed for term in parsed_query.related]:
        if term in term_docs_lookup:
            candidates.update(term_docs_lookup[term].postings.keys())
    for term in [term.stemmed for term in parsed_query.required]:
        if term in term_docs_lookup:
            candidates &= set(term_docs_lookup[term].postings.keys())
        else:
            return set()
    return candidates

def phrase_search(query_terms, document_id, term_docs_lookup, stats):
    if not query_terms:
        return False
    if document_id not in stats.document_length:
        return False

    for term in query_terms:
        stemmed_term = term.stemmed
        if stemmed_term not in term_docs_lookup or document_id not in term_docs_lookup[stemmed_term].postings:
            return False

    first_term = query_terms[0].stemmed
    candidate_positions = term_docs_lookup[first_term].postings[document_id].positions

    for i in range(1, len(query_terms)):
        stemmed_term = query_terms[i].stemmed
        term_positions = set(term_docs_lookup[stemmed_term].postings[document_id].positions)
        candidate_positions = [
            pos for pos in candidate_positions
            if (pos + i) in term_positions
        ]
        if not candidate_positions:
            return False

    return True

def apply_operators(parsed_query, relevant_docs, term_docs_lookup, pages):
    filtered = set(relevant_docs)

    for term in [term.stemmed for term in parsed_query.excluded]:
        if term in term_docs_lookup:
            excluded_docs = set(term_docs_lookup[term].postings.keys())
            filtered -= excluded_docs

    for term in [term.stemmed for term in parsed_query.required]:
        if term in term_docs_lookup:
            required_docs = set(term_docs_lookup[term].postings.keys())
            filtered &= required_docs
        else:
            return set()

    if parsed_query.site_filter:
        site = parsed_query.site_filter.lower()
        filtered = {
            doc_id for doc_id in filtered
            if urlparse(doc_id).netloc.lower().endswith(site)
        }

    if parsed_query.intitle:
        def title_contains_terms(doc_id):
            title = pages[doc_id].title.lower() if doc_id in pages else ""
            return all(term.original.lower() in title for term in parsed_query.intitle)

        filtered = {
            doc_id
            for doc_id in filtered
            if title_contains_terms(doc_id)
        }

    if parsed_query.inurl:
        def url_contains_terms(doc_id):
            return all(term.original.lower() in doc_id.lower() for term in parsed_query.inurl)

        filtered = {doc_id for doc_id in filtered if url_contains_terms(doc_id)}

    if parsed_query.related:
        def related_contains_terms(doc_id):
            return all(term.original.lower() in doc_id.lower() for term in parsed_query.related)

        filtered = {
            doc_id
            for doc_id in filtered
            if related_contains_terms(doc_id)
        }

    return filtered