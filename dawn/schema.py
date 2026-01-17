from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, Field


class Event(BaseModel):
    event_id: str
    company: str
    published_at: datetime
    source_type: str
    publisher: str
    title: str
    url: Optional[HttpUrl] = None
    text: str
    theme: str
    sentiment: str
    impact_score: float = Field(ge=0, le=1)
    is_trigger_event: bool
