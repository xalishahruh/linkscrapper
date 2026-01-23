from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from backend.app.db import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, index=True)
    input_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    result_json = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
