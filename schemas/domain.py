from datetime import datetime

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class RobotRule(BaseModel):
    user_agent: str = "*"
    disallowed_paths: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)


class Domain(Document):
    host: Indexed(str, unique=True)
    robots_rules: list[RobotRule] = Field(default_factory=list)
    robots_fetched_at: datetime | None = None
    crawl_delay: float | None = None
    last_request_at: datetime | None = None

    class Settings:
        name = "domains"
