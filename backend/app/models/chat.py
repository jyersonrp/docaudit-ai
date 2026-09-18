from typing import Optional, List
from pydantic import BaseModel, Field

class Citation(BaseModel):
    chunk_id: str
    page_number: int
    snippet: str
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    section: Optional[str] = None

class ChatQueryRequest(BaseModel):
    question: str
    doc_id: str
    top_k: int = 4
    provider: Optional[str] = None

class ChatResponse(BaseModel):
    doc_id: str
    question: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    provider_used: str
