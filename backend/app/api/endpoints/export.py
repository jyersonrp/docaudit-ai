from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from app.workers.audit_worker import AuditWorker
from app.services.export.report_generator import ReportGenerator

router = APIRouter()

@router.get("/{doc_id}/pdf")
async def export_pdf(doc_id: str):
    """
    Downloads executive publication-grade audit report in PDF format.
    """
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    audit = AuditWorker.get_audit_result(doc_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit result not ready yet")

    pdf_bytes = ReportGenerator.generate_pdf(audit, meta)
    filename = f"DocAudit_Report_{meta.filename.rsplit('.', 1)[0]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{doc_id}/markdown", response_class=PlainTextResponse)
async def export_markdown(doc_id: str):
    """
    Downloads executive audit report in Markdown format.
    """
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    audit = AuditWorker.get_audit_result(doc_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit result not ready yet")

    md_content = ReportGenerator.generate_markdown(audit, meta)
    filename = f"DocAudit_Report_{meta.filename.rsplit('.', 1)[0]}.md"

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{doc_id}/json")
async def export_json(doc_id: str):
    """
    Downloads structured raw audit data in JSON format.
    """
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    audit = AuditWorker.get_audit_result(doc_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit result not ready yet")

    data = ReportGenerator.generate_json(audit, meta)
    return JSONResponse(content=data)
