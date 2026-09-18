import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.models.document import DocumentMetadata, DocumentStatus, DocumentType
from app.models.audit import AuditResult
from app.services.document.extractor import DocumentExtractor
from app.services.document.chunker import DocumentChunker
from app.services.vector.store import vector_store
from app.services.ai.factory import LLMFactory

logger = logging.getLogger(__name__)

class AuditWorker:
    @staticmethod
    def _get_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(str(settings.DB_PATH), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls) -> None:
        with cls._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    status_message TEXT,
                    progress INTEGER DEFAULT 0,
                    audit_type TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT
                )
            """)
            conn.commit()

    @classmethod
    def save_metadata(cls, meta: DocumentMetadata) -> None:
        with cls._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents (
                    id, filename, file_type, file_size, total_pages, total_chunks,
                    status, status_message, progress, audit_type, created_at, updated_at, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.id,
                meta.filename,
                meta.file_type,
                meta.file_size,
                meta.total_pages,
                meta.total_chunks,
                meta.status.value,
                meta.status_message,
                meta.progress,
                meta.audit_type.value if meta.audit_type else None,
                meta.created_at.isoformat(),
                meta.updated_at.isoformat(),
                meta.error
            ))
            conn.commit()

    @classmethod
    def get_metadata(cls, doc_id: str) -> Optional[DocumentMetadata]:
        with cls._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentMetadata(
                id=row["id"],
                filename=row["filename"],
                file_type=row["file_type"],
                file_size=row["file_size"],
                total_pages=row["total_pages"],
                total_chunks=row["total_chunks"],
                status=DocumentStatus(row["status"]),
                status_message=row["status_message"],
                progress=row["progress"],
                audit_type=DocumentType(row["audit_type"]) if row["audit_type"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                error=row["error"]
            )

    @classmethod
    def list_documents(cls) -> List[DocumentMetadata]:
        with cls._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                DocumentMetadata(
                    id=row["id"],
                    filename=row["filename"],
                    file_type=row["file_type"],
                    file_size=row["file_size"],
                    total_pages=row["total_pages"],
                    total_chunks=row["total_chunks"],
                    status=DocumentStatus(row["status"]),
                    status_message=row["status_message"],
                    progress=row["progress"],
                    audit_type=DocumentType(row["audit_type"]) if row["audit_type"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    error=row["error"]
                )
                for row in rows
            ]

    @classmethod
    def save_audit_result(cls, audit: AuditResult) -> None:
        file_path = settings.STORAGE_DIR / f"{audit.doc_id}_audit.json"
        file_path.write_text(audit.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def get_audit_result(cls, doc_id: str) -> Optional[AuditResult]:
        file_path = settings.STORAGE_DIR / f"{doc_id}_audit.json"
        if not file_path.exists():
            return None
        try:
            content = file_path.read_text(encoding="utf-8")
            return AuditResult.model_validate_json(content)
        except Exception as e:
            logger.error(f"Error loading audit result for {doc_id}: {e}")
            return None

    @classmethod
    async def process_document_pipeline(
        cls, 
        doc_id: str, 
        file_path: Path, 
        audit_type: DocumentType, 
        provider_name: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> None:
        meta = cls.get_metadata(doc_id)
        if not meta:
            logger.error(f"Cannot process document {doc_id}: metadata not found")
            return

        try:
            # 1. EXTRACTING
            meta.status = DocumentStatus.EXTRACTING
            meta.status_message = "Extracting document pages and textual content..."
            meta.progress = 20
            meta.audit_type = audit_type
            meta.updated_at = datetime.now(timezone.utc)
            cls.save_metadata(meta)

            pages = DocumentExtractor.extract(file_path, meta.file_type)
            meta.total_pages = len(pages)
            full_text = "\n\n".join([f"--- Page {p['page_number']} ---\n{p['text']}" for p in pages])

            # 2. CHUNKING & INDEXING
            meta.status = DocumentStatus.INDEXING
            meta.status_message = "Generating semantic chunks and indexing into vector store..."
            meta.progress = 50
            meta.updated_at = datetime.now(timezone.utc)
            cls.save_metadata(meta)

            chunks = DocumentChunker.chunk_document(doc_id, pages)
            meta.total_chunks = len(chunks)
            vector_store.delete_doc(doc_id)
            vector_store.add_chunks(chunks)

            # 3. AUDITING WITH LLM FACTORY
            meta.status = DocumentStatus.AUDITING
            meta.status_message = f"Performing {audit_type.value} audit via AI engine..."
            meta.progress = 75
            meta.updated_at = datetime.now(timezone.utc)
            cls.save_metadata(meta)

            provider = LLMFactory.get_provider(provider_name)
            
            legal_audit = None
            financial_audit = None
            custom_audit = None

            if audit_type == DocumentType.LEGAL:
                legal_audit = await provider.audit_legal(full_text, chunks)
            elif audit_type == DocumentType.FINANCIAL:
                financial_audit = await provider.audit_financial(full_text, chunks)
            elif audit_type == DocumentType.CUSTOM:
                custom_audit = await provider.audit_custom(full_text, chunks, custom_prompt)

            audit_result = AuditResult(
                doc_id=doc_id,
                audit_type=audit_type,
                completed_at=datetime.now(timezone.utc),
                provider_used=provider.provider_name,
                model_used=provider.model_name,
                legal_audit=legal_audit,
                financial_audit=financial_audit,
                custom_audit=custom_audit
            )
            cls.save_audit_result(audit_result)

            # 4. COMPLETED
            meta.status = DocumentStatus.COMPLETED
            meta.status_message = f"Audit complete ({provider.provider_name.upper()} - {provider.model_name})"
            meta.progress = 100
            meta.updated_at = datetime.now(timezone.utc)
            cls.save_metadata(meta)
            logger.info(f"Successfully processed document {doc_id}")

        except Exception as e:
            logger.exception(f"Pipeline error for doc {doc_id}: {e}")
            meta.status = DocumentStatus.FAILED
            meta.status_message = f"Processing failed: {str(e)}"
            meta.error = str(e)
            meta.progress = 0
            meta.updated_at = datetime.now(timezone.utc)
            cls.save_metadata(meta)

# Initialize document table on import
AuditWorker.init_db()
