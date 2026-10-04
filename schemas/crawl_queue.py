from datetime import datetime, timezone
from typing import Literal
from beanie import Document, Indexed
from pydantic import Field

class CrawlQueue(Document):
    url: Indexed(str, unique=True)
    status: Literal["pending", "crawling", "completed", "failed"] = "pending"
    priority_score: int = 0
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "crawl_queue"
