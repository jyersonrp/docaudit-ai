from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.document import DocumentType, DocumentStatus
from app.models.audit import AuditResult
from app.workers.audit_worker import AuditWorker
from app.services.ai.factory import LLMFactory
from app.core.config import settings

router = APIRouter()

@router.get("/providers", response_model=List[Dict[str, Any]])
async def list_providers():
    """
    Returns available AI providers, dynamic connectivity status, and default recommendations.
    """
    return await LLMFactory.list_providers_async()

@router.get("/{doc_id}/result", response_model=AuditResult)
async def get_audit_result(doc_id: str):
    """
    Retrieves the structured Pydantic audit result for a completed document.
    """
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    if meta.status == DocumentStatus.FAILED:
        raise HTTPException(status_code=400, detail=f"Audit failed: {meta.error or meta.status_message}")

    if meta.status in (DocumentStatus.PENDING, DocumentStatus.EXTRACTING, DocumentStatus.INDEXING, DocumentStatus.AUDITING):
        raise HTTPException(status_code=202, detail=f"Audit in progress. Status: {meta.status.value} ({meta.progress}%)")

    result = AuditWorker.get_audit_result(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found")
    return result

@router.post("/{doc_id}/rerun")
async def rerun_audit(
    doc_id: str,
    background_tasks: BackgroundTasks,
    audit_type: Optional[DocumentType] = None,
    provider: Optional[str] = None,
    custom_prompt: Optional[str] = None
):
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    # Locate original file in upload dir
    clean_prefix = f"{doc_id}_"
    matched_files = list(settings.UPLOAD_DIR.glob(f"{clean_prefix}*"))
    if not matched_files:
        raise HTTPException(status_code=404, detail="Original source file not found on disk")

    selected_type = audit_type or meta.audit_type or DocumentType.LEGAL

    # Invalidate caches and purge stale audit file before re-triggering
    from app.services.cache.memory_cache import audit_cache, query_cache
    audit_cache.invalidate(f"audit_result:{doc_id}")
    query_cache.clear()
    stale_audit_file = settings.STORAGE_DIR / f"{doc_id}_audit.json"
    if stale_audit_file.exists():
        try:
            stale_audit_file.unlink()
        except Exception:
            pass

    # Immediately reset metadata status
    meta.status = DocumentStatus.PENDING
    meta.status_message = "Re-queued for audit pipeline"
    meta.progress = 5
    meta.audit_type = selected_type
    meta.error = None
    AuditWorker.save_metadata(meta)

    background_tasks.add_task(
        AuditWorker.process_document_pipeline,
        doc_id=doc_id,
        file_path=matched_files[0],
        audit_type=selected_type,
        provider_name=provider,
        custom_prompt=custom_prompt
    )

    return {"message": f"Audit pipeline re-triggered for {doc_id}", "status": "QUEUED"}
