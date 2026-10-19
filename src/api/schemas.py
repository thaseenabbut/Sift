from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]