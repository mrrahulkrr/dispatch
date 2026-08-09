from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class DispatchState(BaseModel):
    section_slug: str
    watch_topic: str
    since_timestamp: Optional[datetime] = None
    raw_docs: list[dict] = Field(default_factory=list)
    classified_docs: list[dict] = Field(default_factory=list)
    summaries: list[dict] = Field(default_factory=list)
    synthesis: Optional[str] = None
    digest_draft: list[dict] = Field(default_factory=list)
    approval_status: Literal["pending", "approved", "rejected", "edited"] = "pending"
    delivered_at: Optional[datetime] = None
