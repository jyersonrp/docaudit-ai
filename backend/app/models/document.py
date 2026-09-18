from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    INDEXING = "INDEXING"
    AUDITING = "AUDITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentType(str, Enum):
    LEGAL = "legal"
    FINANCIAL = "financial"
    CUSTOM = "custom"

class DocumentChunk(BaseModel):
    id: str
    doc_id: str
    page_number: int
    chunk_index: int
    content: str
    token_count: int = 0
    section: Optional[str] = None
    embedding: Optional[List[float]] = None

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    total_pages: int = 0
    total_chunks: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    status_message: str = "Awaiting processing"
    progress: int = 0 # 0 - 100
    audit_type: Optional[DocumentType] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    file_size: int
    file_type: str
    status: DocumentStatus
    message: str
