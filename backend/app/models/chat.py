from typing import Optional, List
from pydantic import BaseModel, Field

class Citation(BaseModel):
    chunk_id: str
    page_number: int
    snippet: str
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    section: Optional[str] = None

class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000, description="User question")
    doc_id: str = Field(..., min_length=1, max_length=64, description="Document ID")
    top_k: int = Field(default=4, ge=1, le=20, description="Top K relevant chunks")
    provider: Optional[str] = Field(default=None, max_length=50)

class ChatResponse(BaseModel):
    doc_id: str
    question: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    provider_used: str
