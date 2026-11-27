from rich import print

from schemas.page import Page
from schemas.search_index import IndexStats, TermDocument
from src.cache import generate_cache_key, get_cached_results, set_cached_results
from src.query_parser import parse_query
from src.results import results
from src.retrieval.hybrid import hybrid_search
from storage.vectordb import VectorDB

vector_db = VectorDB()


async def search(query, bm25_parameters, redis_manager, proximity_weight):
    stats = await IndexStats.find_one({"id_name": "global_stats"})

    if not stats:
        print("Search index stats not found. Have you crawled and indexed yet?")
        return

    key = generate_cache_key(
        query,
        bm25_parameters,
        stats.index_version,
        proximity_weight,
    )

    try:
        cached_results = await get_cached_results(redis_manager, key)

        if cached_results is not None:
            print("[bold green][CACHE HIT][/bold green]")
            return cached_results
        else:
            print("[bold yellow][CACHE MISS][/bold yellow]")

    except (ConnectionError, TimeoutError) as e:
        print(
            f"[bold red][ERROR][/bold red] "
            f"Could not connect to Redis. {type(e).__name__}: {e}"
        )

    parsed = parse_query(query)

    all_stemmed_terms = set()

    all_stemmed_terms.update(t.stemmed for t in parsed.terms)

    for phrase in parsed.phrases:
        all_stemmed_terms.update(t.stemmed for t in phrase)

    all_stemmed_terms.update(t.stemmed for t in parsed.intitle)
    all_stemmed_terms.update(t.stemmed for t in parsed.inurl)
    all_stemmed_terms.update(t.stemmed for t in parsed.related)
    all_stemmed_terms.update(t.stemmed for t in parsed.required)
    all_stemmed_terms.update(t.stemmed for t in parsed.excluded)

    # Fetch matching term documents from MongoDB
    term_docs_list = await TermDocument.find(
        {"term": {"$in": list(all_stemmed_terms)}}
    ).to_list()

    term_docs_lookup = {
        td.term: td for td in term_docs_list
    }

    candidate_docs = {
        url
        for term_doc in term_docs_lookup.values()
        for url in term_doc.postings_by_url.keys()  # noqa: SIM118
    }

    relevant_pages_list = await Page.find(
        {"url": {"$in": list(candidate_docs)}}
    ).to_list()

    pages_lookup = {
        page.url: page for page in relevant_pages_list
    }

    scored_docs, ranking_terms = await hybrid_search(
        query,
        parsed,
        term_docs_lookup,
        pages_lookup,
        stats,
        bm25_parameters,
        proximity_weight,
        vector_db,
    )

    result_data = []

    await results(
        scored_docs,
        pages_lookup,
        ranking_terms,
        term_docs_lookup,
        result_data,
    )

    # Cache results in Redis
    try:
        await set_cached_results(redis_manager, key, result_data)

    except (ConnectionError, TimeoutError) as e:
        print(
            f"[bold red][ERROR][/bold red] "
            f"Could not write to Redis cache. {type(e).__name__}: {e}"
        )

    return result_data
