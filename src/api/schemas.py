from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    count: int
    total: int
    page: int
    page_size: int
    results: list[SearchResult]