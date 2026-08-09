import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Digest(Base):
    __tablename__ = "digests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_slug = Column(String, nullable=False)
    thread_id = Column(String, nullable=False)
    watch_topic = Column(String, nullable=False)
    synthesis = Column(String, nullable=True)
    digest_draft = Column(JSONB, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=False)
