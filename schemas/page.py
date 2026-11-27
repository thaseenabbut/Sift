from datetime import UTC, datetime

from beanie import Document, Indexed
from pydantic import Field


class Page(Document):
    url: Indexed(str, unique=True)
    aliases: list[str] = Field(default_factory=list)
    title: str | None = None
    meta_description: str | None = None
    clean_text: str
    h1_headers: list[str] = Field(default_factory=list)
    content_hash: str = ""
    # Set only after chunks and embeddings for ``content_hash`` have been
    # persisted successfully.  This lets a later crawl retry a failed vector
    # write without treating the page content itself as changed.
    chunk_content_hash: str = ""
    page_rank_score: float = 0.0
    last_crawled_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    
    class Settings:
        name = "pages"
