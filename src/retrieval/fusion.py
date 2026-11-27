
def reciprocal_rank_fusion(
    keyword_results: list[tuple[str, float]],
    semantic_results: list[dict],
    pages_lookup: dict,
    k: int = 60,
) -> list[tuple[str, float]]:

    fused_scores = {}

    for rank, (url, _) in enumerate(keyword_results, start=1):
        fused_scores[url] = fused_scores.get(url, 0.0) + (
            1.0 / (k + rank)
        )

    id_to_url = {
        page.id: page.url
        for page in pages_lookup.values()
    }

    seen_pages = set()

    for rank, result in enumerate(semantic_results, start=1):
        page_id = result["page_id"]

        if page_id in seen_pages:
            continue

        seen_pages.add(page_id)

        url = id_to_url.get(page_id)

        if url is None:
            continue

        fused_scores[url] = fused_scores.get(url, 0.0) + (
            1.0 / (k + rank)
        )

    ranked_results = sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return ranked_results
