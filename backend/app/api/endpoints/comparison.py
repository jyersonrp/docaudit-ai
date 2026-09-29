import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Response, status
from app.core.config import settings
from app.models.comparison import ComparativeAuditResult, ComparisonRequest
from app.models.document import DocumentMetadata, DocumentStatus, DocumentType
from app.workers.audit_worker import AuditWorker
from app.services.ai.factory import LLMFactory
from app.services.export.report_generator import ReportGenerator
from app.services.cache.memory_cache import audit_cache

logger = logging.getLogger(__name__)
router = APIRouter()

COMPARISON_STORAGE_DIR = settings.STORAGE_DIR / "comparisons"
COMPARISON_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_V1_BASELINE = """
MASTER SERVICES AGREEMENT (BASELINE VERSION 1.0)
Date: January 15, 2024
Parties: Acme Enterprise Solutions Inc. ("Vendor") and Global Nexus Financial Corp. ("Customer").

1. SERVICES AND TERM
Vendor shall provide cloud infrastructure monitoring and analytics. The initial term is two (2) years.
Either party may terminate this Agreement without cause upon sixty (60) days prior written notice.

2. FEES AND PAYMENTS
Customer agrees to pay all undisputed invoices within thirty (30) days of receipt.

3. LIMITATION OF LIABILITY
EXCEPT FOR WILLFUL MISCONDUCT OR BREACH OF CONFIDENTIALITY, IN NO EVENT SHALL EITHER PARTY BE LIABLE
FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES. EACH PARTY'S TOTAL AGGREGATE LIABILITY
ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL BE STRICTLY LIMITED TO THE FEES PAID OR PAYABLE BY
CUSTOMER TO VENDOR IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM, NOT TO EXCEED $50,000 USD.

4. INDEMNIFICATION
Each party agrees to mutually defend, indemnify, and hold harmless the other party against direct third-party
claims arising from the indemnifying party's gross negligence or willful infringement of valid intellectual property.

5. SERVICE LEVEL AGREEMENT (SLA)
Vendor guarantees 99.5% service availability per calendar month. For any availability shortfall, Customer
shall receive proportional recurring service credits applied against subsequent monthly invoices.

6. GOVERNING LAW AND JURISDICTION
This Agreement shall be governed by the laws of the State of Delaware, USA, without regard to conflict of laws.
The parties submit to the exclusive jurisdiction of the federal and state courts in New Castle County, Delaware.
"""

SAMPLE_V2_REDLINE = """
MASTER SERVICES AGREEMENT (COUNTERPARTY REVISION 2.0 - REDLINE DRAFT)
Date: February 02, 2024
Parties: Acme Enterprise Solutions Inc. ("Vendor") and Global Nexus Financial Corp. ("Customer").

1. SERVICES AND TERM
Vendor shall provide cloud infrastructure monitoring. The initial term is two (2) years.
[REDLINE AMENDMENT]: Customer may terminate this Agreement at any time, with or without cause, upon seven (7) days
written notice. Vendor shall possess no termination for convenience rights whatsoever.

2. FEES AND PAYMENTS
Customer may withhold disputed or offset payments in its sole discretion for up to one hundred twenty (120) days.

3. LIMITATION OF LIABILITY
[REDLINE AMENDMENT - MONETARY CAP STRICKEN]: NEITHER PARTY'S LIABILITY UNDER THIS AGREEMENT SHALL BE SUBJECT
TO ANY FINANCIAL CEILING, MONETARY CAP, OR LIABILITY LIMITATION. UNLIMITED LIABILITY SHALL APPLY TO ALL DIRECT,
INDIRECT, CONSEQUENTIAL, AND PUNITIVE LOSSES.

4. INDEMNIFICATION
[REDLINE AMENDMENT - ONE-SIDED EXTENSION]: Vendor shall defend, indemnify, and hold harmless Customer from any and all
third-party claims, regulatory inquiries, investigation costs, or losses arising directly or indirectly out of the Services.

5. SERVICE LEVEL AGREEMENT (SLA)
[REDLINE AMENDMENT - CASH PENALTY]: Vendor guarantees 99.99% continuous availability. Any outage exceeding 0.01%
shall trigger immediate cash liquidated damages of $10,000 USD per downtime hour, payable within fifteen (15) days.

6. GOVERNING LAW AND JURISDICTION
[REDLINE AMENDMENT - INTERNATIONAL ARBITRATION]: This Agreement shall be governed by English Law. All disputes shall be
finally settled by binding commercial arbitration under the Rules of the London Court of International Arbitration (LCIA).
"""

def _save_comparison(comparison: ComparativeAuditResult) -> None:
    path = COMPARISON_STORAGE_DIR / f"{comparison.id}.json"
    path.write_text(comparison.model_dump_json(indent=2), encoding="utf-8")
    audit_cache.set(f"comparison:{comparison.id}", comparison)

def _load_comparison(comparison_id: str) -> Optional[ComparativeAuditResult]:
    cached = audit_cache.get(f"comparison:{comparison_id}")
    if cached:
        return cached
    path = COMPARISON_STORAGE_DIR / f"{comparison_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        result = ComparativeAuditResult.model_validate(data)
        audit_cache.set(f"comparison:{comparison_id}", result)
        return result
    except Exception as e:
        logger.error(f"Failed to read comparison {comparison_id}: {e}")
        return None

@router.post("", response_model=ComparativeAuditResult, status_code=status.HTTP_200_OK)
async def compare_documents(request: ComparisonRequest):
    """
    Execute a side-by-side comparative redline risk audit between two documents.
    """
    if request.doc1_id == request.doc2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a document against itself. Please select two distinct documents."
        )

    meta1 = AuditWorker.get_metadata(request.doc1_id)
    if not meta1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Baseline document {request.doc1_id} not found.")

    meta2 = AuditWorker.get_metadata(request.doc2_id)
    if not meta2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Revision document {request.doc2_id} not found.")

    doc1_audit = AuditWorker.load_audit_result(request.doc1_id)
    doc2_audit = AuditWorker.load_audit_result(request.doc2_id)

    # Read extracted text
    text1 = ""
    text2 = ""
    f1 = settings.UPLOAD_DIR / f"{request.doc1_id}_{meta1.filename}"
    f2 = settings.UPLOAD_DIR / f"{request.doc2_id}_{meta2.filename}"

    if f1.exists():
        try:
            from app.services.document.extractor import DocumentExtractor
            pages1 = DocumentExtractor.extract(f1, meta1.file_type)
            text1 = "\n\n".join([p["text"] for p in pages1])
        except Exception:
            text1 = meta1.filename
    else:
        text1 = meta1.filename

    if f2.exists():
        try:
            from app.services.document.extractor import DocumentExtractor
            pages2 = DocumentExtractor.extract(f2, meta2.file_type)
            text2 = "\n\n".join([p["text"] for p in pages2])
        except Exception:
            text2 = meta2.filename
    else:
        text2 = meta2.filename

    provider = LLMFactory.get_provider(request.provider)
    doc_type = meta1.audit_type or meta2.audit_type or DocumentType.LEGAL

    comparison = await provider.compare_documents(
        doc1_id=meta1.id,
        doc1_name=meta1.filename,
        doc1_text=text1,
        doc1_audit=doc1_audit,
        doc2_id=meta2.id,
        doc2_name=meta2.filename,
        doc2_text=text2,
        doc2_audit=doc2_audit,
        doc_type=doc_type
    )

    _save_comparison(comparison)
    return comparison

@router.post("/sample-pair", status_code=status.HTTP_200_OK)
async def seed_and_compare_sample_pair(provider: Optional[str] = Query(None)):
    """
    Seed a ready-to-inspect comparative sample pair (MSA v1 Standard vs MSA v2 Redline)
    and execute the comparative redline audit instantly.
    """
    id1 = f"sample-msa-v1-{uuid.uuid4().hex[:6]}"
    id2 = f"sample-msa-v2-{uuid.uuid4().hex[:6]}"

    f1_name = "Master-Services-Agreement-v1.0-Standard.txt"
    f2_name = "Master-Services-Agreement-v2.0-Redline-Counterparty.txt"

    p1 = settings.UPLOAD_DIR / f"{id1}_{f1_name}"
    p2 = settings.UPLOAD_DIR / f"{id2}_{f2_name}"

    p1.write_text(SAMPLE_V1_BASELINE, encoding="utf-8")
    p2.write_text(SAMPLE_V2_REDLINE, encoding="utf-8")

    meta1 = DocumentMetadata(
        id=id1,
        filename=f1_name,
        file_type="txt",
        file_size=len(SAMPLE_V1_BASELINE.encode("utf-8")),
        status=DocumentStatus.COMPLETED,
        status_message="Seeded Baseline MSA v1.0",
        progress=100,
        audit_type=DocumentType.LEGAL
    )
    meta2 = DocumentMetadata(
        id=id2,
        filename=f2_name,
        file_type="txt",
        file_size=len(SAMPLE_V2_REDLINE.encode("utf-8")),
        status=DocumentStatus.COMPLETED,
        status_message="Seeded Counterparty Redline MSA v2.0",
        progress=100,
        audit_type=DocumentType.LEGAL
    )
    AuditWorker.save_metadata(meta1)
    AuditWorker.save_metadata(meta2)

    # Execute single document audits in background if not already present
    import asyncio
    asyncio.create_task(AuditWorker.process_document_pipeline(id1, p1, DocumentType.LEGAL, provider))
    asyncio.create_task(AuditWorker.process_document_pipeline(id2, p2, DocumentType.LEGAL, provider))

    # Run comparison
    prov = LLMFactory.get_provider(provider)
    comparison = await prov.compare_documents(
        doc1_id=id1,
        doc1_name=f1_name,
        doc1_text=SAMPLE_V1_BASELINE,
        doc1_audit=None,
        doc2_id=id2,
        doc2_name=f2_name,
        doc2_text=SAMPLE_V2_REDLINE,
        doc2_audit=None,
        doc_type=DocumentType.LEGAL
    )

    _save_comparison(comparison)
    return {
        "comparison": comparison,
        "doc1": meta1,
        "doc2": meta2
    }

@router.get("/{comparison_id}", response_model=ComparativeAuditResult)
async def get_comparison(comparison_id: str):
    """
    Fetch an existing comparative audit result by ID.
    """
    result = _load_comparison(comparison_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comparison {comparison_id} not found.")
    return result

@router.get("/{comparison_id}/pdf")
async def export_comparison_pdf(comparison_id: str):
    """
    Download publication-grade executive Redline Comparison PDF.
    """
    comparison = _load_comparison(comparison_id)
    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comparison {comparison_id} not found.")

    pdf_bytes = ReportGenerator.generate_comparison_pdf(comparison)
    filename = f"DocAudit_Comparative_Redline_{comparison.doc1_id[:6]}_vs_{comparison.doc2_id[:6]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
