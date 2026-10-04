from typing import Dict, List
from beanie import Document
from pydantic import BaseModel, Field


class Posting(BaseModel):
    tf: int = 0
    positions: List[int] = Field(default_factory=list)


class TermEntry(BaseModel):
    postings: Dict[str, Posting] = Field(default_factory=dict)


class SearchIndex(Document):
    inverted_index: Dict[str, TermEntry] = Field(default_factory=dict)
    document_length: Dict[str, int] = Field(default_factory=dict)
    document_frequency: Dict[str, int] = Field(default_factory=dict)
    avg_document_length: float = 0.0
    total_documents: int = 0

    class Settings:
        name = "search_index"
