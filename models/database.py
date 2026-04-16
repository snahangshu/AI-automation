from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class KnowledgeDoc(BaseModel):
    """Model for RAG knowledge snippets stored in Supabase."""
    id: Optional[str] = None
    url: str
    title: str
    content: str
    embedding: Optional[List[float]] = None

class Message(BaseModel):
    """Model for a single message in a conversation."""
    role: str
    content: str

class SessionLog(BaseModel):
    """Model for a full conversation session stored in MongoDB."""
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    transcript: List[Message]
    audio_id: Optional[str] = None # Pointer to GridFS file ID

class CompanyProfile(BaseModel):
    """Model for core company information used by agents."""
    name: str = "Fastigo Technology Private Limited"
    description: str
    faq: List[str] = []
