import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from app.core.config import settings
from app.models.document import DocumentMetadata, DocumentStatus, DocumentType, DocumentUploadResponse
from app.workers.audit_worker import AuditWorker
from app.services.vector.store import vector_store

router = APIRouter()

SAMPLE_LEGAL_CONTRACT = """
MASTER SERVICES AND LICENSE AGREEMENT

This Master Services and License Agreement ("Agreement") is entered into as of January 15, 2025 ("Effective Date"),
by and between Apex Enterprise Solutions Inc., a Delaware corporation having its principal office at 100 Tech Blvd, Wilmington, DE ("Provider"),
and Global Retail Logistics Corp., a California corporation having its office at 500 Market St, San Francisco, CA ("Customer").

1. SCOPE OF SERVICES AND LICENSED SOFTWARE
Provider agrees to deliver enterprise document audit and logistics platform software ("Services") as outlined in Exhibit A.
Customer is granted a non-exclusive, non-transferable, revocable license to access the platform during the Term.

2. TERM AND TERMINATION
2.1 Term: This Agreement shall commence on the Effective Date and shall remain in effect for an initial term of two (2) years.
2.2 Termination for Convenience: Customer may terminate this Agreement at any time upon thirty (30) days prior written notice to Provider.
Provider may only terminate upon sixty (60) days written notice if Customer fails to rectify payment arrears.
2.3 Termination for Cause: Either party may terminate immediately if the other party breaches any material term and fails to cure such breach within fifteen (15) days of receipt of written notice.

3. FEES AND PAYMENT TERMS
Customer agrees to pay all undisputed invoices within thirty (30) days of receipt. Late payments shall accrue interest at the rate of 1.5% per month.

4. INDEMNIFICATION AND DEFENSE
Customer shall defend, indemnify, and hold harmless Provider, its affiliates, directors, officers, and employees from and against any and all claims,
damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or related to Customer's data,
unauthorized use of the platform, or alleged infringement of third-party intellectual property rights.

5. LIMITATION OF LIABILITY
EXCEPT FOR CLAIMS ARISING UNDER SECTION 4 (INDEMNIFICATION) OR SECTION 6 (CONFIDENTIALITY), IN NO EVENT SHALL EITHER PARTY'S TOTAL AGGREGATE
LIABILITY UNDER OR IN CONNECTION WITH THIS AGREEMENT EXCEED THE TOTAL FEES ACTUALLY PAID BY CUSTOMER TO PROVIDER IN THE TWELVE (12) MONTHS
PRECEDING THE EVENT GIVING RISE TO LIABILITY. NEITHER PARTY SHALL BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES.

6. CONFIDENTIALITY AND RESTRICTIVE COVENANTS
Each party agrees to protect the Confidential Information of the other party with the same degree of care it uses for its own confidential data,
but not less than reasonable care. For a period of twelve (12) months following the termination of this Agreement, Customer agrees not to solicit
or hire any technical employee or contractor of Provider without prior written consent.

7. GOVERNING LAW AND DISPUTE RESOLUTION
This Agreement shall be governed by and construed in accordance with the internal laws of the State of Delaware, without giving effect to any
choice or conflict of law provision. Any legal suit, action, or proceeding shall be instituted exclusively in the federal or state courts located in New Castle County, Delaware.
"""

SAMPLE_FINANCIAL_REPORT = """
CONSOLIDATED FINANCIAL STATEMENTS AND AUDIT REPORT
For the Fiscal Year Ended December 31, 2024
Apex Technologies International Corp.

INDEPENDENT AUDITOR'S REPORT
To the Board of Directors and Shareholders of Apex Technologies International Corp.:
We have audited the accompanying consolidated balance sheets, consolidated statements of operations, and cash flows.
In our opinion, the consolidated financial statements present fairly, in all material respects, the financial position
of the Company as of December 31, 2024, in conformity with U.S. Generally Accepted Accounting Principles (U.S. GAAP).
Audit Opinion: Unqualified / Clean Opinion.

CONSOLIDATED STATEMENT OF OPERATIONS
(In thousands of USD, except per share data)
- Total Revenue: $248,500
  - Subscription Software Revenue: $192,000
  - Professional Services Revenue: $56,500
- Cost of Revenues: $64,200
- Gross Profit: $184,300 (Gross Margin: 74.2%)
- Operating Expenses:
  - Research & Development: $72,400
  - Sales & Marketing: $54,100
  - General & Administrative: $21,300
- Total Operating Expenses: $147,800
- Operating Income: $36,500 (Operating Margin: 14.7%)
- Net Income: $28,900

BALANCE SHEET HIGHLIGHTS & LIQUIDITY
- Cash and Cash Equivalents: $84,200
- Accounts Receivable: $31,500
- Total Current Assets: $122,800
- Total Current Liabilities: $45,200 (Current Ratio: 2.72x)
- Long-Term Debt: $32,000
- Stockholders' Equity: $118,600 (Debt-to-Equity Ratio: 0.27x)

CONTINGENT LIABILITIES & RISK DISCLOSURES
1. Legal Proceedings: The Company is subject to an ongoing patent assertion litigation in the Eastern District of Texas.
   Management, in consultation with outside counsel, believes the claim is without merit; however, unfavorable resolution could result
   in potential licensing royalties estimated between $3.0M and $5.0M.
2. Tax Exposures: Transfer pricing documentation across European subsidiaries remains under review by foreign revenue authorities.
   A reserve of $1.8M has been accrued for uncertain tax positions under ASC 740.
"""

from app.core.security import verify_magic_bytes, sanitize_filename, safe_join_path
from app.services.cache.memory_cache import audit_cache, query_cache

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    audit_type: DocumentType = Form(DocumentType.LEGAL),
    provider: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None)
):
    original_filename = file.filename or "document.txt"
    sanitized_name = sanitize_filename(original_filename)
    ext = Path(sanitized_name).suffix.lower()
    
    if ext not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: .pdf, .docx, .txt, .md"
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Enterprise magic bytes verification
    if not verify_magic_bytes(file_bytes, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content or signature for format '{ext}'. File header verification failed."
        )

    doc_id = str(uuid.uuid4())[:8]
    clean_filename = f"{doc_id}_{sanitized_name}"
    
    try:
        save_path = safe_join_path(settings.UPLOAD_DIR, clean_filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path validation failed: {str(e)}"
        )
        
    save_path.write_bytes(file_bytes)

    meta = DocumentMetadata(
        id=doc_id,
        filename=sanitized_name,
        file_type=ext,
        file_size=file_size,
        status=DocumentStatus.PENDING,
        status_message="Queued for extraction & audit",
        audit_type=audit_type
    )
    AuditWorker.save_metadata(meta)

    # Trigger background pipeline
    background_tasks.add_task(
        AuditWorker.process_document_pipeline,
        doc_id=doc_id,
        file_path=save_path,
        audit_type=audit_type,
        provider_name=provider,
        custom_prompt=custom_prompt
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=sanitized_name,
        file_size=file_size,
        file_type=ext,
        status=DocumentStatus.PENDING,
        message="Document uploaded successfully. Audit pipeline running in background."
    )

@router.post("/sample", response_model=DocumentUploadResponse)
async def load_sample_document(
    background_tasks: BackgroundTasks,
    sample_type: DocumentType = DocumentType.LEGAL,
    provider: Optional[str] = None
):
    """
    Creates an immediate sample document (Legal or Financial) for 1-click demonstration without needing to search for a file.
    """
    doc_id = f"demo-{sample_type.value}-{str(uuid.uuid4())[:4]}"
    if sample_type == DocumentType.FINANCIAL:
        filename = "Sample_Apex_FY24_Financial_Statements.txt"
        content = SAMPLE_FINANCIAL_REPORT
    else:
        filename = "Sample_Master_Services_Agreement_2025.txt"
        content = SAMPLE_LEGAL_CONTRACT

    save_path = settings.UPLOAD_DIR / f"{doc_id}_{filename}"
    save_path.write_text(content.strip(), encoding="utf-8")

    meta = DocumentMetadata(
        id=doc_id,
        filename=filename,
        file_type=".txt",
        file_size=save_path.stat().st_size,
        status=DocumentStatus.PENDING,
        status_message="Sample queued for audit pipeline",
        audit_type=sample_type
    )
    AuditWorker.save_metadata(meta)

    background_tasks.add_task(
        AuditWorker.process_document_pipeline,
        doc_id=doc_id,
        file_path=save_path,
        audit_type=sample_type,
        provider_name=provider
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=filename,
        file_size=meta.file_size,
        file_type=".txt",
        status=DocumentStatus.PENDING,
        message="Sample document created. Audit pipeline executing in background."
    )

@router.get("", response_model=List[DocumentMetadata])
async def list_documents():
    return AuditWorker.list_documents()

@router.get("/{doc_id}", response_model=DocumentMetadata)
async def get_document(doc_id: str):
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")
    return meta

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    meta = AuditWorker.get_metadata(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    vector_store.delete_doc(doc_id)
    audit_cache.invalidate(f"audit_result:{doc_id}")
    query_cache.clear()
    audit_file = settings.STORAGE_DIR / f"{doc_id}_audit.json"
    if audit_file.exists():
        audit_file.unlink()

    # Clean up uploaded files matching doc_id
    for f in settings.UPLOAD_DIR.glob(f"{doc_id}_*"):
        try:
            f.unlink()
        except Exception as e:
            pass

    # remove from db
    with AuditWorker._get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()

    return {"message": f"Document {doc_id} successfully deleted"}
