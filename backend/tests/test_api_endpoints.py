import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.document import DocumentType

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "active_provider" in data

def test_list_providers():
    res = client.get("/api/v1/audit/providers")
    assert res.status_code == 200
    assert len(res.json()) >= 4

def test_sample_document_pipeline_and_audit():
    # 1. Trigger sample legal contract upload
    res = client.post("/api/v1/documents/sample?sample_type=legal")
    assert res.status_code == 200
    data = res.json()
    doc_id = data["doc_id"]
    assert doc_id is not None

    # 2. Check metadata
    res_meta = client.get(f"/api/v1/documents/{doc_id}")
    assert res_meta.status_code == 200
    meta = res_meta.json()
    assert meta["id"] == doc_id
    assert meta["status"] == "COMPLETED"
    assert meta["total_pages"] >= 1
    assert meta["total_chunks"] >= 1

    # 3. Check audit result
    res_audit = client.get(f"/api/v1/audit/{doc_id}/result")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["audit_type"] == "legal"
    assert audit_data["legal_audit"]["overall_risk_score"] > 0
    assert len(audit_data["legal_audit"]["key_findings"]) >= 1

    # 4. Test RAG Chat
    res_chat = client.post(
        "/api/v1/chat/query",
        json={"question": "What is the liability cap under this contract?", "doc_id": doc_id, "top_k": 3}
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert "answer" in chat_data
    assert len(chat_data["citations"]) >= 1
    assert chat_data["citations"][0]["page_number"] == 1

    # 5. Test Export
    res_md = client.get(f"/api/v1/export/{doc_id}/markdown")
    assert res_md.status_code == 200
    assert "# DocAudit AI Executive Report" in res_md.text

    res_json = client.get(f"/api/v1/export/{doc_id}/json")
    assert res_json.status_code == 200
    assert res_json.json()["metadata"]["id"] == doc_id

    res_pdf = client.get(f"/api/v1/export/{doc_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF")

    # 6. Delete document
    res_del = client.delete(f"/api/v1/documents/{doc_id}")
    assert res_del.status_code == 200

def test_sample_financial_pipeline_and_audit():
    res = client.post("/api/v1/documents/sample?sample_type=financial")
    assert res.status_code == 200
    data = res.json()
    doc_id = data["doc_id"]

    # Check audit result
    res_audit = client.get(f"/api/v1/audit/{doc_id}/result")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["audit_type"] == "financial"
    fin = audit_data["financial_audit"]
    assert fin is not None
    assert fin["total_revenue"] is not None
    assert fin["auditor_opinion"] is not None
    assert len(fin["key_findings"]) >= 1

    # Check export markdown contains financial checklists and exposures
    res_md = client.get(f"/api/v1/export/{doc_id}/markdown")
    assert res_md.status_code == 200
    assert "Financial Health Executive Summary" in res_md.text
    assert "Compliance & Accounting Standards Checklist" in res_md.text

    # Check PDF export
    res_pdf = client.get(f"/api/v1/export/{doc_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF")

    # Clean up
    client.delete(f"/api/v1/documents/{doc_id}")

def test_file_upload_pipeline_and_cleanup(tmp_path):
    from app.core.config import settings
    # Create test document file
    test_file = tmp_path / "nda_sample.txt"
    test_file.write_text("This Non-Disclosure Agreement between Corp Alpha and Beta Inc. Governing law is New York. Termination upon 30 days notice.")

    with open(test_file, "rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": ("nda_sample.txt", f, "text/plain")},
            data={"audit_type": "legal", "provider": "mock"}
        )
    assert res.status_code == 200
    doc_id = res.json()["doc_id"]

    # Verify upload file exists in upload dir
    upload_matches = list(settings.UPLOAD_DIR.glob(f"{doc_id}_*"))
    assert len(upload_matches) == 1

    # Verify rerun endpoint
    res_rerun = client.post(f"/api/v1/audit/{doc_id}/rerun")
    assert res_rerun.status_code == 200

    # Verify deletion cleans up both database and upload directory
    res_del = client.delete(f"/api/v1/documents/{doc_id}")
    assert res_del.status_code == 200
    upload_matches_after = list(settings.UPLOAD_DIR.glob(f"{doc_id}_*"))
    assert len(upload_matches_after) == 0

def test_upload_empty_file_rejected():
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        data={"audit_type": "legal"}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_upload_unsupported_format_rejected():
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.exe", b"fake binary data", "application/octet-stream")},
        data={"audit_type": "legal"}
    )
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()

def test_chat_with_unrelated_query_no_hallucinated_citations():
    # Create legal sample
    res = client.post("/api/v1/documents/sample?sample_type=legal")
    doc_id = res.json()["doc_id"]

    # Query with completely unrelated terms
    res_chat = client.post(
        "/api/v1/chat/query",
        json={"question": "interstellar quantum spacecraft engine astrophysics", "doc_id": doc_id, "provider": "mock"}
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    # Should cleanly state no relevant text found and return zero false citations
    assert len(chat_data["citations"]) == 0
    assert "no relevant text found" in chat_data["answer"].lower()

    # Clean up
    client.delete(f"/api/v1/documents/{doc_id}")
