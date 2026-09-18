from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.document import DocumentType

class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AuditFinding(BaseModel):
    id: str = Field(description="Unique finding identifier, e.g., FIND-001")
    category: str = Field(description="Category of the finding, e.g., 'Termination Clause', 'Liability', 'Fiscal Risk'")
    title: str = Field(description="Short, descriptive title of the audit finding")
    description: str = Field(description="In-depth analysis and rationale of the finding")
    severity: SeverityLevel = Field(description="Severity impact: LOW, MEDIUM, HIGH, or CRITICAL")
    impact: str = Field(description="Business or legal consequence if unaddressed")
    recommendation: str = Field(description="Concrete actionable remediation advice")
    page_number: Optional[int] = Field(default=None, description="Page number where the clause was detected")
    quote: Optional[str] = Field(default=None, description="Direct verbatim excerpt from the document")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")

class RiskMatrixItem(BaseModel):
    dimension: str = Field(description="Risk dimension, e.g., 'Legal Liability', 'Regulatory Compliance', 'Operational Continuity'")
    score: int = Field(ge=0, le=100, description="Numerical score 0-100 where higher means higher risk")
    level: RiskLevel = Field(description="Risk tier: LOW, MEDIUM, HIGH, or CRITICAL")
    summary: str = Field(description="Brief summary of this risk pillar")

class LegalContractAudit(BaseModel):
    parties: List[str] = Field(default_factory=list, description="Identified legal entities entering the agreement")
    effective_date: Optional[str] = Field(default=None, description="Effective start date")
    expiration_date: Optional[str] = Field(default=None, description="Term expiration or renewal date")
    governing_law: Optional[str] = Field(default=None, description="Applicable legal framework/jurisdiction")
    jurisdiction: Optional[str] = Field(default=None, description="Agreed courts or arbitration venue")
    overall_risk_score: int = Field(ge=0, le=100, description="Overall contract risk score from 0 to 100")
    overall_risk_level: RiskLevel = Field(description="Overall risk level")
    executive_summary: str = Field(description="Comprehensive executive summary of the legal audit")
    termination_notice_period: Optional[str] = Field(default=None, description="Notice period required for termination")
    liability_cap: Optional[str] = Field(default=None, description="Total monetary cap on damages")
    indemnification_scope: Optional[str] = Field(default=None, description="Breadth of indemnification obligations")
    non_compete_or_nda: Optional[str] = Field(default=None, description="Restrictive covenants and non-disclosure obligations")
    key_findings: List[AuditFinding] = Field(default_factory=list)
    risk_matrix: List[RiskMatrixItem] = Field(default_factory=list)
    compliance_checklist: Dict[str, bool] = Field(
        default_factory=lambda: {
            "Parties Clearly Identified": True,
            "Clear Governing Law Specified": True,
            "Capped Liability in Place": False,
            "Standard Dispute Resolution": True,
            "Bilateral Termination Rights": False
        }
    )

class FinancialReportAudit(BaseModel):
    company_name: Optional[str] = Field(default=None, description="Audited company or organization name")
    reporting_period: Optional[str] = Field(default=None, description="Fiscal year, quarter, or period covered")
    currency: Optional[str] = Field(default="USD", description="Reporting currency")
    total_revenue: Optional[str] = Field(default=None, description="Top-line gross/net revenue")
    net_income: Optional[str] = Field(default=None, description="Bottom-line net profit/loss")
    operating_margin: Optional[str] = Field(default=None, description="Operating profit margin percentage")
    debt_to_equity: Optional[str] = Field(default=None, description="Debt to equity or leverage ratio")
    auditor_opinion: Optional[str] = Field(default="Unqualified", description="Auditor's opinion type: Unqualified, Qualified, Adverse, Disclaimer")
    overall_risk_score: int = Field(ge=0, le=100, description="Overall financial & reporting risk score (0-100)")
    overall_risk_level: RiskLevel = Field(description="Overall risk level")
    executive_summary: str = Field(description="Executive briefing on financial stability and reporting integrity")
    contingent_liabilities: List[str] = Field(default_factory=list, description="Off-balance sheet obligations or legal disputes")
    fiscal_risks: List[str] = Field(default_factory=list, description="Tax exposures and solvency concerns")
    key_findings: List[AuditFinding] = Field(default_factory=list)
    risk_matrix: List[RiskMatrixItem] = Field(default_factory=list)
    compliance_checklist: Dict[str, bool] = Field(
        default_factory=lambda: {
            "Auditor Report Included": True,
            "GAAP/IFRS Standards Met": True,
            "Going Concern Assessment Passed": True,
            "Revenue Recognition Verified": True,
            "Debt Covenants in Compliance": True
        }
    )

class CustomAudit(BaseModel):
    audit_name: str = Field(default="Custom Audit", description="Name or objective of the custom audit")
    overall_risk_score: int = Field(ge=0, le=100)
    overall_risk_level: RiskLevel
    executive_summary: str
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Extracted dynamic key-value pairs")
    key_findings: List[AuditFinding] = Field(default_factory=list)
    risk_matrix: List[RiskMatrixItem] = Field(default_factory=list)
    compliance_checklist: Dict[str, bool] = Field(default_factory=dict)

class AuditResult(BaseModel):
    doc_id: str
    audit_type: DocumentType
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_used: str
    model_used: str
    legal_audit: Optional[LegalContractAudit] = None
    financial_audit: Optional[FinancialReportAudit] = None
    custom_audit: Optional[CustomAudit] = None
