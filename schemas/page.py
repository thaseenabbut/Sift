from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field

class Page(Document):
    url: Indexed(str, unique=True)
    title: Optional[str] = None
    meta_description: Optional[str] = None
    clean_text: str
    h1_headers: List[str] = Field(default_factory=list)
    page_rank_score: float = 0.0
    last_crawled_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    class Settings:
        name = "pages"