import logging

from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from src.search import search
from src.ranker import bm25_parameters
from src.api.schemas import SearchResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse)
async def get_search(
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
        
    try:
        results = await search(query, bm25_parameters)
        
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