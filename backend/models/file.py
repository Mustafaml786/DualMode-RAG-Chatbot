# backend/models/file.py
import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class File(Base):
    __tablename__ = 'files'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True), index=True) # <-- ADD THIS LINE
    filename = Column(String)
    uploaded_at = Column(DateTime, default=func.now())