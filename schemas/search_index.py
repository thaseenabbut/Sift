from typing import Any, Dict, List, Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field, PrivateAttr, field_validator

class Posting(BaseModel):
    url: str
    tf: int = 0
    positions: List[int] = Field(default_factory=list)

class TermDocument(Document):
    term: Indexed(str, unique=True)
    document_frequency: int = 0
    postings: List[Posting] = Field(default_factory=list)
    _postings_by_url: Optional[Dict[str, Posting]] = PrivateAttr(default=None)

    @field_validator("postings", mode="before")
    @classmethod
    def coerce_postings(cls, value: Any) -> Any:
        # Older indexes stored postings as {url: {tf, positions}} instead of a list.
        if isinstance(value, dict):
            return [
                {"url": url, **posting} if isinstance(posting, dict) else posting
                for url, posting in value.items()
            ]
        return value

    @property
    def postings_by_url(self) -> Dict[str, Posting]:
        if self._postings_by_url is None:
            self._postings_by_url = {p.url: p for p in self.postings}
        return self._postings_by_url

    class Settings:
        name = "term_documents"

class IndexStats(Document):
    id_name: Indexed(str, unique=True) = "global_stats"
    document_length: Dict[str, int] = Field(default_factory=dict)
    avg_document_length: float = 0.0
    total_documents: int = 0

    class Settings:
        name = "index_stats"
