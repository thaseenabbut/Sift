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
    time_taken: float | None = None
    results: list[SearchResult]