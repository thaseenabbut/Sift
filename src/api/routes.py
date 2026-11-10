import logging
import math

from fastapi import APIRouter, HTTPException, Query, Request
from pymongo.errors import PyMongoError

from src.search import search
from src.ranker import bm25_parameters
from src.ranker import proximity_weight
from src.api.schemas import SearchResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse)
async def get_search(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )
        
    rate_limiter = request.app.state.rate_limiter
    client_ip = request.client.host if request.client else "unknown"

    if not await rate_limiter.consume(client_ip):
        _, remaining, retry_after = await rate_limiter.check(client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": str(math.ceil(retry_after)),
                "X-RateLimit-Limit": str(rate_limiter.max_tokens),
                "X-RateLimit-Remaining": str(remaining),
            },
        )
        
    try:
        redis_manager = request.app.state.redis_manager
        results = await search(query, bm25_parameters, redis_manager, proximity_weight)
        
    except PyMongoError:
        logger.exception("Database error while processing search query.")
        raise HTTPException(
            status_code=503,
            detail="Search service is temporarily unavailable.",
        )
        
    except Exception:
        logger.exception("Unexpected error while processing search query.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while searching.",
        )

    if results is None:
        raise HTTPException(
            status_code=503,
            detail="Search index is not available.",
        )

    total = len(results)
    start = (page - 1) * page_size
    page_results = results[start : start + page_size]

    return {
        "query": query,
        "count": len(results),
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": page_results,
    }