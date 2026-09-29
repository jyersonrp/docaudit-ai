import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.document import DocumentType
from app.models.comparison import ComparativeAuditResult, RiskDelta, DiffChangeType, RiskImpactType
from app.services.ai.mock_provider import MockProvider
from app.services.export.report_generator import ReportGenerator

client = TestClient(app)

@pytest.mark.asyncio
async def test_mock_provider_compare_legal():
    provider = MockProvider()
    doc1_text = "Master Services Agreement v1. Liability limited to $50,000. Mutual termination with 60 days notice. Delaware law."
    doc2_text = "Master Services Agreement v2. Unlimited liability. Customer may terminate on 7 days notice. English law and LCIA arbitration."
    
    res = await provider.compare_documents(
        doc1_id="doc-1",
        doc1_name="MSA_v1.pdf",
        doc1_text=doc1_text,
        doc1_audit=None,
        doc2_id="doc-2",
        doc2_name="MSA_v2_Redline.pdf",
        doc2_text=doc2_text,
        doc2_audit=None,
        doc_type=DocumentType.LEGAL
    )
    
    assert isinstance(res, ComparativeAuditResult)
    assert res.doc1_id == "doc-1"
    assert res.doc2_id == "doc-2"
    assert res.risk_delta.score_delta > 0
    assert len(res.clause_diffs) >= 4
    assert len(res.key_takeaways) >= 2
    assert len(res.renegotiation_strategy) >= 2
    
    # Verify critical escalation detected
    escalations = [d for d in res.clause_diffs if d.risk_impact == RiskImpactType.CRITICAL_ESCALATION]
    assert len(escalations) >= 1

@pytest.mark.asyncio
async def test_mock_provider_compare_financial():
    provider = MockProvider()
    doc1_text = "Apex Tech Consolidated Balance Sheet 2023. Gross profit $184M. Gross margin 74%. Debt to equity 0.27x. Unqualified opinion."
    doc2_text = "Apex Tech Consolidated Balance Sheet 2024. Gross profit $120M. Gross margin 62%. Debt to equity 0.85x. Qualified opinion."
    
    res = await provider.compare_documents(
        doc1_id="fin-1",
        doc1_name="10K_2023.pdf",
        doc1_text=doc1_text,
        doc1_audit=None,
        doc2_id="fin-2",
        doc2_name="10K_2024.pdf",
        doc2_text=doc2_text,
        doc2_audit=None,
        doc_type=DocumentType.FINANCIAL
    )
    
    assert isinstance(res, ComparativeAuditResult)
    assert len(res.metric_comparisons) >= 2
    assert any(m.is_risk_increase for m in res.metric_comparisons)

def test_comparison_pdf_generation():
    provider = MockProvider()
    import asyncio
    res = asyncio.run(provider.compare_documents(
        doc1_id="d1",
        doc1_name="MSA_Standard.pdf",
        doc1_text="Sample text 1",
        doc1_audit=None,
        doc2_id="d2",
        doc2_name="MSA_Redline.pdf",
        doc2_text="Sample text 2",
        doc2_audit=None,
        doc_type=DocumentType.LEGAL
    ))
    
    pdf_bytes = ReportGenerator.generate_comparison_pdf(res)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000

def test_seed_sample_pair_endpoint():
    response = client.post("/api/v1/compare/sample-pair")
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data
    assert "doc1" in data
    assert "doc2" in data
    cmp_res = data["comparison"]
    assert cmp_res["doc1_id"].startswith("sample-msa-v1")
    assert cmp_res["doc2_id"].startswith("sample-msa-v2")
    assert cmp_res["risk_delta"]["score_delta"] > 0
    assert len(cmp_res["clause_diffs"]) >= 3

def test_compare_endpoint_validation():
    # Comparing same doc
    res = client.post("/api/v1/compare", json={"doc1_id": "same_id", "doc2_id": "same_id"})
    assert res.status_code == 400
    assert "Cannot compare a document against itself" in res.json()["detail"]

    # Non-existent doc
    res_not_found = client.post("/api/v1/compare", json={"doc1_id": "fake_1", "doc2_id": "fake_2"})
    assert res_not_found.status_code == 404

def test_comparison_pdf_endpoint():
    # First seed sample pair
    seed_res = client.post("/api/v1/compare/sample-pair")
    assert seed_res.status_code == 200
    cmp_id = seed_res.json()["comparison"]["id"]

    # Now download PDF
    pdf_res = client.get(f"/api/v1/compare/{cmp_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"]
    assert pdf_res.content.startswith(b"%PDF-")
