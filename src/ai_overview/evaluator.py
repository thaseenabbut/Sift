import math


def evaluation_result(
    sufficient: bool,
    reason: str | None = None,
    metrics: dict | None = None,
) -> dict:
    return {
        "sufficient": sufficient,
        "reason": reason,
        "metrics": metrics if metrics is not None else {},
    }


def evaluate_evidence(
    query: str,
    context: dict,
    chunks: list[dict],
) -> dict:
    if not query or not query.strip():
        return evaluation_result(sufficient=False, reason="EMPTY_QUERY")

    if not context or not isinstance(context.get("context"), str) or not context["context"].strip():
        return evaluation_result(sufficient=False, reason="EMPTY_CONTEXT")

    if not context.get("sources"):
        return evaluation_result(sufficient=False, reason="MISSING_SOURCES")

    if not chunks:
        return evaluation_result(sufficient=False, reason="MISSING_CHUNKS")

    usable_chunks = [
        chunk
        for chunk in chunks
        if isinstance(chunk.get("text"), str) and chunk["text"].strip()
    ]

    if not usable_chunks:
        return evaluation_result(sufficient=False, reason="NO_USABLE_CHUNKS")

    scores = [
        chunk["score"]
        for chunk in usable_chunks
        if isinstance(chunk.get("score"), (int, float))
        and not isinstance(chunk.get("score"), bool)
        and math.isfinite(chunk["score"])
    ]

    if not scores:
        return evaluation_result(sufficient=False, reason="NO_VALID_SIMILARITY_SCORES")

    average_score = sum(scores) / len(scores)
    max_score = max(scores)
    strong_chunks = sum(score >= average_score for score in scores)
    score_spread = max_score - min(scores)
    context_word_count = len(context["context"].split())

    metrics = {
        "average_score": round(average_score, 4),
        "max_score": round(max_score, 4),
        "strong_chunks": strong_chunks,
        "score_spread": round(score_spread, 4),
        "context_word_count": context_word_count,
        "scored_chunk_count": len(scores),
        "usable_chunk_count": len(usable_chunks),
    }

    return evaluation_result(
        sufficient=True,
        reason=None,
        metrics=metrics,
    )
