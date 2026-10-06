from typing import Dict, List
from beanie import Document, Indexed
from pydantic import BaseModel, Field

class Posting(BaseModel):
    tf: int = 0
    positions: List[int] = Field(default_factory=list)

class TermDocument(Document):
    term: Indexed(str, unique=True)
    document_frequency: int = 0
    postings: Dict[str, Posting] = Field(default_factory=dict)

    class Settings:
        name = "term_documents"

class IndexStats(Document):
    id_name: Indexed(str, unique=True) = "global_stats"
    document_length: Dict[str, int] = Field(default_factory=dict)
    avg_document_length: float = 0.0
    total_documents: int = 0

    class Settings:
        name = "index_stats"
