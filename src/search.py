from retriever import phrase_search
from query_parser import parse_query
from retriever import retrieve, apply_operators
from ranker import score_document
from results import results
from schemas.search_index import TermDocument, IndexStats
from schemas.page import Page

async def search(query, bm25_parameters):
    stats = await IndexStats.find_one(IndexStats.id_name == "global_stats")
    if not stats:
        print("Search index stats not found. Have you crawled and indexed yet?")
        return

    scored_docs = []
    parsed = parse_query(query)
    
    all_stemmed_terms = set()
    all_stemmed_terms.update([t.stemmed for t in parsed.terms])
    for phrase in parsed.phrases:
        all_stemmed_terms.update([t.stemmed for t in phrase])
    all_stemmed_terms.update([t.stemmed for t in parsed.intitle])
    all_stemmed_terms.update([t.stemmed for t in parsed.inurl])
    all_stemmed_terms.update([t.stemmed for t in parsed.related])
    all_stemmed_terms.update([t.stemmed for t in parsed.required])
    all_stemmed_terms.update([t.stemmed for t in parsed.excluded])
    
    term_docs_list = await TermDocument.find({"term": {"$in": list(all_stemmed_terms)}}).to_list()
    term_docs_lookup = {td.term: td for td in term_docs_list}
    
    relevant_docs = retrieve(parsed, term_docs_lookup)
    
    relevant_pages_list = await Page.find({"url": {"$in": list(relevant_docs)}}).to_list()
    pages_lookup = {page.url: page for page in relevant_pages_list}

    relevant_docs = apply_operators(parsed, relevant_docs, term_docs_lookup, pages_lookup)
    
    if parsed.phrases:
        relevant_docs = {
            doc_id 
            for doc_id in relevant_docs
            if all(
                phrase_search(phrase, doc_id, term_docs_lookup, stats) for phrase in parsed.phrases
                )
            }

    for doc_id in relevant_docs:
        ranking_terms = parsed.terms + parsed.required
        score = await score_document(
            ranking_terms,
            doc_id, 
            term_docs_lookup, 
            stats,
            bm25_parameters
        )
        scored_docs.append((doc_id, score))

    scored_docs.sort(key=lambda x: x[1], reverse=True)
    await results(scored_docs, pages_lookup, parsed.terms + parsed.required, term_docs_lookup)