from typing import Literal

from pydantic import BaseModel, Field


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

class OverviewSource(BaseModel):
    title: str
    url: str

class AIOverviewResponse(BaseModel):
    status: Literal[
        "GENERATED_SUCCESSFULLY",
        "NOT_GENERATED_DUE_TO_INSUFFICIENT_EVIDENCE",
        "NOT_GENERATED_DUE_TO_LLM_ERROR",
        "NOT_GENERATED_DUE_TO_EMPTY_QUERY",
        "NOT_GENERATED_DUE_TO_RETRIEVAL_ERROR",
    ]
    reason: str | None = None
    overview: str | None = None
    sources: list[OverviewSource] = Field(default_factory=list)