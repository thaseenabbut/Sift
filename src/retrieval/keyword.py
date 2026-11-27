from src.ranker import build_idf_cache, collect_ranking_terms, score_document
from src.retriever import apply_operators, phrase_search, retrieve


def keyword_search(
    parsed,
    term_docs_lookup,
    pages_lookup,
    stats,
    bm25_parameters,
    proximity_weight,
):
    # retrieve candidate documents
    relevant_docs = retrieve(parsed, term_docs_lookup)

    # apply query operators
    relevant_docs = apply_operators(
        parsed,
        relevant_docs,
        term_docs_lookup,
        pages_lookup,
    )

    # verify phrase matches
    if parsed.phrases:
        relevant_docs = {
            doc_id
            for doc_id in relevant_docs
            if all(
                phrase_search(
                    phrase,
                    doc_id,
                    term_docs_lookup,
                    stats,
                )
                for phrase in parsed.phrases
            )
        }

    # collect ranking terms
    ranking_terms = collect_ranking_terms(parsed)

    # build IDF cache
    idf_cache = build_idf_cache(
        ranking_terms,
        term_docs_lookup,
        stats,
    )

    # calculate document scores
    scored_docs = []

    for doc_id in relevant_docs:
        score = score_document(
            ranking_terms,
            doc_id,
            term_docs_lookup,
            stats,
            bm25_parameters,
            idf_cache,
        )

        scored_docs.append((doc_id, score))

    # sort it by relevance
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return scored_docs, ranking_terms
