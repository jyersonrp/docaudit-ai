from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.document import DocumentType
from app.models.audit import RiskLevel

class DiffChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"

class RiskImpactType(str, Enum):
    CRITICAL_ESCALATION = "CRITICAL_ESCALATION" # High negative shift in risk
    ADVERSE = "ADVERSE"                         # Moderate negative shift in risk
    NEUTRAL = "NEUTRAL"                         # Minor or operational shift
    FAVORABLE = "FAVORABLE"                     # Improved protection / lower risk

class ClauseDiff(BaseModel):
    category: str = Field(description="Category of the clause (e.g. 'Liability Cap', 'Termination Notice', 'Indemnification')")
    doc1_clause: Optional[str] = Field(default=None, description="Summary or clause excerpt in baseline Document 1")
    doc2_clause: Optional[str] = Field(default=None, description="Summary or clause excerpt in revised Document 2")
    change_type: DiffChangeType = Field(description="Type of change detected: ADDED, REMOVED, MODIFIED, UNCHANGED")
    risk_impact: RiskImpactType = Field(description="Risk impact assessment on the contracting party")
    analysis: str = Field(description="Detailed commercial and legal reasoning of the modification")

class MetricComparison(BaseModel):
    metric_name: str = Field(description="Name of the metric or ratio compared")
    doc1_value: Optional[str] = Field(default=None, description="Baseline document value")
    doc2_value: Optional[str] = Field(default=None, description="Revision document value")
    change_summary: str = Field(description="Concise description of the delta")
    is_risk_increase: bool = Field(default=False, description="Flag indicating whether this shift worsens risk")

class RiskDelta(BaseModel):
    doc1_score: int = Field(ge=0, le=100, description="Overall risk score for baseline Document 1")
    doc2_score: int = Field(ge=0, le=100, description="Overall risk score for revised Document 2")
    score_delta: int = Field(description="doc2_score minus doc1_score (positive indicates risk increase)")
    doc1_level: RiskLevel = Field(description="Risk tier of Document 1")
    doc2_level: RiskLevel = Field(description="Risk tier of Document 2")
    verdict: str = Field(description="Summary verdict: SIGNIFICANT_RISK_INCREASE, MODERATE_RISK_INCREASE, RISK_DECREASED, NEUTRAL")
    summary: str = Field(description="Narrative explaining the net change in risk profile")

class ComparativeAuditResult(BaseModel):
    id: str = Field(description="Unique comparison identifier")
    doc1_id: str = Field(description="Baseline document ID")
    doc1_name: str = Field(description="Baseline document filename")
    doc2_id: str = Field(description="Revision document ID")
    doc2_name: str = Field(description="Revision document filename")
    doc_type: DocumentType = Field(description="Type of document compared (LEGAL or FINANCIAL)")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_used: str = Field(description="AI provider utilized for the comparison")
    model_used: str = Field(description="Model utilized for the comparison")
    risk_delta: RiskDelta = Field(description="Calculated risk difference and scoring breakdown")
    executive_comparison: str = Field(description="High-level executive briefing for General Counsel or CFO")
    clause_diffs: List[ClauseDiff] = Field(default_factory=list, description="Itemized clause-by-clause redline changes")
    metric_comparisons: List[MetricComparison] = Field(default_factory=list, description="Key operational and financial metrics comparison")
    key_takeaways: List[str] = Field(default_factory=list, description="Key negotiation bullet points")
    renegotiation_strategy: List[str] = Field(default_factory=list, description="Concrete strategic counter-proposals")

class ComparisonRequest(BaseModel):
    doc1_id: str = Field(description="Baseline document ID")
    doc2_id: str = Field(description="Revision document ID")
    provider: Optional[str] = Field(default=None, description="Optional override AI provider")
