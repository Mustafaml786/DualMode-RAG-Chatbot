import uuid
from sqlalchemy import Column, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True)) # links to sessions table id
    role = Column(String) # 'user' or 'assistant'
    message = Column(Text)
    timestamp = Column(DateTime, default=func.now())