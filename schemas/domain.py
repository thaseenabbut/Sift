from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field


class RobotRule(BaseModel):
    user_agent: str = "*"
    disallowed_paths: List[str] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)


class Domain(Document):
    host: Indexed(str, unique=True)
    robots_rules: List[RobotRule] = Field(default_factory=list)
    robots_fetched_at: Optional[datetime] = None
    crawl_delay: Optional[float] = None
    last_request_at: Optional[datetime] = None

    class Settings:
        name = "domains"
