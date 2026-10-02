from retriever import phrase_search
from query_parser import parse_query
from retriever import retrieve, apply_operators
from ranker import score_document
from results import results

def search(query, search_index, bm25_parameters, pages):
    scored_docs = []

    parsed = parse_query(query)
    relevant_docs = retrieve(parsed, search_index)
    relevant_docs = apply_operators(parsed, relevant_docs, search_index, pages)
    
    if parsed.phrases:
        relevant_docs = {
            doc_id 
            for doc_id in relevant_docs
            if all(
                phrase_search(phrase, doc_id, search_index) for phrase in parsed.phrases
                )
            }

    for doc_id in relevant_docs:
        score = score_document(
            parsed.terms + parsed.required, 
            doc_id, 
            search_index, 
            bm25_parameters
        )
        scored_docs.append((doc_id, score))

    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return results(scored_docs, pages)