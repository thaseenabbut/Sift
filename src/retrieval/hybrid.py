from src.retrieval.fusion import reciprocal_rank_fusion
from src.retrieval.keyword import keyword_search
from src.retrieval.semantic import semantic_search
from src.retriever import apply_operators, phrase_search


async def hybrid_search(
    query,
    parsed,
    term_docs_lookup,
    pages_lookup,
    stats,
    bm25_parameters,
    proximity_weight,
    vector_db,
    keyword_limit=100,
    semantic_limit=100,
):

    keyword_results, ranking_terms = keyword_search(
        parsed,
        term_docs_lookup,
        pages_lookup,
        stats,
        bm25_parameters,
        proximity_weight,
    )

    keyword_results = keyword_results[:keyword_limit]

    semantic_results = await semantic_search(
        query,
        vector_db,
        limit=semantic_limit,
    )

    semantic_page_ids = {
        result["page_id"]
        for result in semantic_results
    }

    from schemas.page import Page

    semantic_pages = await Page.find(
        {"_id": {"$in": list(semantic_page_ids)}}
    ).to_list()

    for page in semantic_pages:
        pages_lookup[page.url] = page

    semantic_candidates = {
        page.url for page in semantic_pages
    }

    semantic_candidates = apply_operators(
        parsed,
        semantic_candidates,
        term_docs_lookup,
        pages_lookup,
    )

    if parsed.phrases:
        semantic_candidates = {
            url
            for url in semantic_candidates
            if all(
                phrase_search(
                    phrase,
                    url,
                    term_docs_lookup,
                    stats,
                )
                for phrase in parsed.phrases
            )
        }

    semantic_results = [
        result
        for result in semantic_results
        if next(
            (
                page.url
                for page in semantic_pages
                if page.id == result["page_id"]
            ),
            None,
        ) in semantic_candidates
    ]

    fused_results = reciprocal_rank_fusion(
        keyword_results,
        semantic_results,
        pages_lookup,
)

    return fused_results, ranking_terms
