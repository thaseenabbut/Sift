from document_parser import parser
from stemmer import stem
from retriever import retrieve, phrase_search
from ranker import score_document
from results import results

def search(query, search_index, bm25_parameters, pages):
    scored_docs = []
    
    is_phrase_query = query.startswith('"') and query.endswith('"')
    query_terms = stem(parser(query))
    relevant_docs = retrieve(query_terms, search_index)
    
    if is_phrase_query:
        relevant_docs = {
            doc_id for doc_id in relevant_docs
            if phrase_search(query_terms, doc_id, search_index)
        }
        
    for doc_id in relevant_docs:
        score = score_document(query_terms, doc_id, search_index, bm25_parameters)
        scored_docs.append((doc_id, score))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return results(scored_docs, pages)