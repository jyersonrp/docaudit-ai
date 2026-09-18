import pytest
from datetime import datetime, timezone
from app.models.document import DocumentMetadata, DocumentStatus, DocumentType
from app.models.audit import AuditResult, LegalContractAudit, RiskLevel
from app.services.export.report_generator import ReportGenerator

@pytest.fixture
def sample_audit():
    legal = LegalContractAudit(
        parties=["Acme Corp", "Beta LLC"],
        overall_risk_score=55,
        overall_risk_level=RiskLevel.MEDIUM,
        executive_summary="Legal audit completed with moderate exposure.",
        termination_notice_period="30 days",
        liability_cap="$1,000,000",
        key_findings=[],
        risk_matrix=[],
        compliance_checklist={"Governing Law Present": True}
    )
    meta = DocumentMetadata(
        id="test-doc",
        filename="Test_Agreement.pdf",
        file_type=".pdf",
        file_size=1024,
        status=DocumentStatus.COMPLETED
    )
    audit = AuditResult(
        doc_id="test-doc",
        audit_type=DocumentType.LEGAL,
        completed_at=datetime.now(timezone.utc),
        provider_used="mock",
        model_used="heuristic-rule-engine-v1",
        legal_audit=legal
    )
    return audit, meta

def test_generate_markdown(sample_audit):
    audit, meta = sample_audit
    md = ReportGenerator.generate_markdown(audit, meta)
    assert "# DocAudit AI Executive Report" in md
    assert "Acme Corp" in md
    assert "MEDIUM" in md
    assert "$1,000,000" in md

def test_generate_json(sample_audit):
    audit, meta = sample_audit
    data = ReportGenerator.generate_json(audit, meta)
    assert "metadata" in data
    assert "audit_result" in data
    assert data["audit_result"]["legal_audit"]["overall_risk_score"] == 55

def test_generate_pdf(sample_audit):
    audit, meta = sample_audit
    pdf_bytes = ReportGenerator.generate_pdf(audit, meta)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    # PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")

def test_generate_financial_and_custom_reports():
    from app.models.audit import FinancialReportAudit, CustomAudit, AuditFinding, SeverityLevel, RiskMatrixItem

    meta = DocumentMetadata(
        id="fin-doc",
        filename="Q4_Report.pdf",
        file_type=".pdf",
        file_size=2048,
        status=DocumentStatus.COMPLETED
    )

    fin = FinancialReportAudit(
        company_name="Apex Global Corp",
        reporting_period="FY 2024",
        total_revenue="$250,000,000",
        net_income="$35,000,000",
        operating_margin="14%",
        debt_to_equity="0.30",
        auditor_opinion="Unqualified",
        overall_risk_score=25,
        overall_risk_level=RiskLevel.LOW,
        executive_summary="Solid balance sheet and low debt ratio.",
        contingent_liabilities=["Delaware pending IP litigation"],
        fiscal_risks=["EU transfer pricing review"],
        key_findings=[
            AuditFinding(
                id="F1",
                category="Revenue",
                title="Revenue > $200M & Growing",
                description="Strong performance < 5% variance & clean books.",
                severity=SeverityLevel.LOW,
                impact="Positive solvency impact.",
                recommendation="Maintain current reserves.",
                page_number=1,
                quote="Total revenue exceeded expectations."
            )
        ],
        risk_matrix=[
            RiskMatrixItem(dimension="Solvency", score=20, level=RiskLevel.LOW, summary="Safe buffer")
        ]
    )
    audit_fin = AuditResult(
        doc_id="fin-doc",
        audit_type=DocumentType.FINANCIAL,
        provider_used="mock",
        model_used="heuristic",
        financial_audit=fin
    )

    # Test markdown includes financial sections
    md = ReportGenerator.generate_markdown(audit_fin, meta)
    assert "Apex Global Corp" in md
    assert "Delaware pending IP litigation" in md
    assert "EU transfer pricing review" in md
    assert "Compliance & Accounting Standards Checklist" in md

    # Test PDF generation with special characters (<, >, &) does not crash
    pdf_bytes = ReportGenerator.generate_pdf(audit_fin, meta)
    assert pdf_bytes.startswith(b"%PDF")

    # Test Custom Audit Report
    cust = CustomAudit(
        audit_name="GDPR Compliance",
        overall_risk_score=30,
        overall_risk_level=RiskLevel.LOW,
        executive_summary="GDPR Article 28 evaluated.",
        extracted_fields={"subprocessors_count": 4, "dpo_appointed": "Yes"},
        key_findings=[],
        risk_matrix=[],
        compliance_checklist={"DPA Signed": True}
    )
    audit_cust = AuditResult(
        doc_id="cust-doc",
        audit_type=DocumentType.CUSTOM,
        provider_used="mock",
        model_used="heuristic",
        custom_audit=cust
    )
    md_cust = ReportGenerator.generate_markdown(audit_cust, meta)
    assert "GDPR Compliance" in md_cust
    assert "subprocessors_count" in md_cust
    pdf_cust = ReportGenerator.generate_pdf(audit_cust, meta)
    assert pdf_cust.startswith(b"%PDF")
