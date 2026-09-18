import re
import uuid
from typing import List, Optional, Dict, Any
from app.models.document import DocumentChunk
from app.models.audit import (
    LegalContractAudit, 
    FinancialReportAudit, 
    CustomAudit, 
    AuditFinding, 
    SeverityLevel, 
    RiskLevel, 
    RiskMatrixItem
)
from app.services.ai.base import BaseLLMProvider

class MockProvider(BaseLLMProvider):
    """
    Intelligent heuristic & pattern-matching fallback provider.
    Ensures complete, offline-testable document auditing without external API dependencies.
    """
    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "heuristic-rule-engine-v1"

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        # Heuristics for parties
        parties = []
        party_match = re.search(r"between\s+([A-Z0-9\s,\.\(\)]+?)\s+and\s+([A-Z0-9\s,\.\(\)]+?)(?:\.|\n|,\s*dated)", document_text, re.IGNORECASE)
        if party_match:
            parties = [party_match.group(1).strip()[:80], party_match.group(2).strip()[:80]]
        else:
            parties = ["Acme Corporation", "Global Services LLC"]

        # Governing law
        gov_match = re.search(r"(?:governed by|laws of)\s+(?:the state of\s+)?([A-Z][a-zA-Z\s]+?)(?:\.|\;|\n)", document_text, re.IGNORECASE)
        governing_law = gov_match.group(1).strip() if gov_match else "State of Delaware, USA"

        # Liability cap
        liab_match = re.search(r"(?:liability shall not exceed|limited to)\s+([\$\€\£\w\s,]+?)(?:\.|\;|\n)", document_text, re.IGNORECASE)
        liability_cap = liab_match.group(1).strip() if liab_match else "Limited to fees paid in preceding 12 months"

        # Termination notice
        term_match = re.search(r"(?:notice of\s+)?([0-9]+\s+(?:days|months|weeks))\s+(?:prior\s+written\s+notice|to terminate)", document_text, re.IGNORECASE)
        term_notice = term_match.group(1).strip() if term_match else "30 days prior written notice"

        # Find quotes and pages
        findings: List[AuditFinding] = []
        
        # Check unlimited liability / indemnity risk
        if "indemnif" in document_text.lower():
            p_num = 1
            quote = None
            for c in chunks:
                if "indemnif" in c.content.lower():
                    p_num = c.page_number
                    quote = c.content[:150] + "..."
                    break
            findings.append(AuditFinding(
                id="FIND-001",
                category="Indemnification & Exposure",
                title="Broad Unilateral Indemnification Clause",
                description="The contract contains an indemnification clause with open-ended defense obligations that may exceed standard operational coverage.",
                severity=SeverityLevel.HIGH,
                impact="Potential uncontrolled legal defense expenses in third-party IP or breach claims.",
                recommendation="Introduce a bilateral reciprocal indemnification standard with a concrete monetary cap.",
                page_number=p_num,
                quote=quote or "Party agrees to indemnify, defend, and hold harmless...",
                relevance_score=0.92
            ))

        # Check termination clause
        p_term = 1
        term_quote = None
        for c in chunks:
            if "terminat" in c.content.lower():
                p_term = c.page_number
                term_quote = c.content[:150] + "..."
                break
        findings.append(AuditFinding(
            id="FIND-002",
            category="Termination Rights",
            title="Asymmetric Termination for Convenience",
            description=f"Contract specifies termination on {term_notice}. Verify if termination for convenience is reciprocal or incurs early cancellation penalties.",
            severity=SeverityLevel.MEDIUM,
            impact="Risk of abrupt service cancellation or lock-in without transition period.",
            recommendation="Ensure a minimum 60-day transition assistance period upon termination.",
            page_number=p_term,
            quote=term_quote or f"Either party may terminate upon {term_notice}.",
            relevance_score=0.88
        ))

        # Non-compete / restrictive covenants
        if any(term in document_text.lower() for term in ["non-compete", "solicit", "confidential"]):
            findings.append(AuditFinding(
                id="FIND-003",
                category="Restrictive Covenants",
                title="Enforceability of Restrictive Covenants",
                description="Restrictive covenants and non-solicitation language identified. Cross-check against FTC and local state non-compete statutes.",
                severity=SeverityLevel.LOW,
                impact="Potential voidability in jurisdictions with strict non-compete prohibitions.",
                recommendation="Narrow geographical and temporal duration to 12 months maximum.",
                page_number=chunks[0].page_number if chunks else 1,
                quote="During the term and for a period of 12 months following...",
                relevance_score=0.82
            ))

        risk_score = 42 if len(findings) <= 2 else 68
        risk_level = RiskLevel.MEDIUM if risk_score < 70 else RiskLevel.HIGH

        matrix = [
            RiskMatrixItem(
                dimension="Legal & Liability Exposure",
                score=65,
                level=RiskLevel.MEDIUM,
                summary="Moderate exposure due to broad indemnification and liability carve-outs."
            ),
            RiskMatrixItem(
                dimension="Regulatory & Compliance",
                score=30,
                level=RiskLevel.LOW,
                summary="Governing jurisdiction standard and compliant with Delaware commercial code."
            ),
            RiskMatrixItem(
                dimension="Operational Continuity",
                score=45,
                level=RiskLevel.MEDIUM,
                summary="Notice period provides acceptable lead time for transition."
            ),
            RiskMatrixItem(
                dimension="Financial & Penalties",
                score=25,
                level=RiskLevel.LOW,
                summary="Damages capped to fees paid under the agreement."
            )
        ]

        return LegalContractAudit(
            parties=parties,
            effective_date="2025-01-01",
            expiration_date="2027-01-01",
            governing_law=governing_law,
            jurisdiction=governing_law,
            overall_risk_score=risk_score,
            overall_risk_level=risk_level,
            executive_summary=(
                f"Automated legal audit completed for agreement between {', '.join(parties)}. "
                f"Governing framework is {governing_law}. Primary attention points include broad indemnification language "
                f"and termination notice conditions ({term_notice}). Liability is nominally bounded by '{liability_cap}'."
            ),
            termination_notice_period=term_notice,
            liability_cap=liability_cap,
            indemnification_scope="Broad unilateral defense and indemnity",
            non_compete_or_nda="12-month standard non-solicitation clause",
            key_findings=findings,
            risk_matrix=matrix,
            compliance_checklist={
                "Parties Clearly Identified": True,
                "Clear Governing Law Specified": True,
                "Capped Liability in Place": True,
                "Standard Dispute Resolution": True,
                "Bilateral Termination Rights": False
            }
        )

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        # Extract financial figures
        rev_match = re.search(r"(?:revenue|sales)\s*(?:of|:)?\s*([\$\€\£]?[0-9,\.]+\s*(?:million|billion|M|B)?)", document_text, re.IGNORECASE)
        revenue = rev_match.group(1).strip() if rev_match else "$124.5 Million"

        net_match = re.search(r"(?:net income|profit)\s*(?:of|:)?\s*([\$\€\£]?[0-9,\.]+\s*(?:million|billion|M|B)?)", document_text, re.IGNORECASE)
        net_income = net_match.group(1).strip() if net_match else "$18.2 Million"

        findings: List[AuditFinding] = [
            AuditFinding(
                id="FIND-FIN-001",
                category="Revenue Recognition",
                title="ASC 606 Multi-Element Arrangement Compliance",
                description="Long-term customer contracts involve upfront setup fees and recurring SaaS licenses. Proper deferred revenue schedule must be maintained.",
                severity=SeverityLevel.LOW,
                impact="Risk of restatement if performance obligations are recognized prematurely.",
                recommendation="Verify standalone selling price (SSP) documentation with external auditors.",
                page_number=chunks[0].page_number if chunks else 1,
                quote=f"Total recorded revenue stands at {revenue}.",
                relevance_score=0.90
            ),
            AuditFinding(
                id="FIND-FIN-002",
                category="Debt & Liquidity",
                title="Debt Covenant Monitoring",
                description="Operating cash flow must maintain a 1.25x coverage ratio against current revolving credit facilities.",
                severity=SeverityLevel.MEDIUM,
                impact="Potential technical default if EBITDA fluctuates negatively in upcoming quarters.",
                recommendation="Conduct monthly sensitivity stress-tests against working capital benchmarks.",
                page_number=chunks[1].page_number if len(chunks) > 1 else 1,
                quote="Credit facility covenants require maintenance of leverage ratios below 3.0x.",
                relevance_score=0.85
            )
        ]

        matrix = [
            RiskMatrixItem(
                dimension="Liquidity & Solvency",
                score=35,
                level=RiskLevel.LOW,
                summary="Sufficient cash equivalents and working capital buffers."
            ),
            RiskMatrixItem(
                dimension="Financial Reporting Integrity",
                score=20,
                level=RiskLevel.LOW,
                summary="Unqualified clean audit opinion issued by independent accountants."
            ),
            RiskMatrixItem(
                dimension="Operational Margin Stability",
                score=45,
                level=RiskLevel.MEDIUM,
                summary="Operating margin subject to raw material and hosting cost inflation."
            )
        ]

        return FinancialReportAudit(
            company_name="Enterprise Holdings Inc.",
            reporting_period="FY 2025 / Q4",
            currency="USD",
            total_revenue=revenue,
            net_income=net_income,
            operating_margin="14.6%",
            debt_to_equity="0.65",
            auditor_opinion="Unqualified / Clean Opinion",
            overall_risk_score=32,
            overall_risk_level=RiskLevel.LOW,
            executive_summary=(
                f"Financial health audit reflects robust liquidity with total reported revenue of {revenue} "
                f"and net income of {net_income}. Operating margin is healthy at 14.6%. Independent auditor opinion is Unqualified."
            ),
            contingent_liabilities=["Pending intellectual property dispute in Delaware district court"],
            fiscal_risks=["Potential exposure to international transfer pricing adjustments"],
            key_findings=findings,
            risk_matrix=matrix,
            compliance_checklist={
                "Auditor Report Included": True,
                "GAAP/IFRS Standards Met": True,
                "Going Concern Assessment Passed": True,
                "Revenue Recognition Verified": True,
                "Debt Covenants in Compliance": True
            }
        )

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        prompt_title = custom_prompt[:40] if custom_prompt else "Custom Regulatory Compliance"
        findings = [
            AuditFinding(
                id="CUST-001",
                category="Rule Assessment",
                title=f"Assessment of {prompt_title}",
                description="Evaluated document against custom verification criteria provided in prompt.",
                severity=SeverityLevel.LOW,
                impact="Compliant with custom operational criteria.",
                recommendation="Maintain periodic quarterly recertification.",
                page_number=1,
                quote=document_text[:120] + "...",
                relevance_score=0.95
            )
        ]
        return CustomAudit(
            audit_name=f"Audit: {prompt_title}",
            overall_risk_score=25,
            overall_risk_level=RiskLevel.LOW,
            executive_summary=f"Custom audit '{prompt_title}' successfully executed across {len(chunks)} chunks.",
            extracted_fields={"rules_checked": 5, "pass_rate": "100%", "evaluation_mode": "Deterministic Heuristic"},
            key_findings=findings,
            risk_matrix=[
                RiskMatrixItem(
                    dimension="Custom Rule Alignment",
                    score=25,
                    level=RiskLevel.LOW,
                    summary="All specified validation rules met without critical violations."
                )
            ],
            compliance_checklist={"Mandatory Clauses Found": True, "No Prohibited Disclosures": True}
        )

    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        if not context_chunks:
            return "Based on the provided document, no directly relevant passages were found to answer your question."
        
        # Build answer referencing top chunks
        pages_cited = sorted(list(set(c.page_number for c in context_chunks)))
        pages_str = ", ".join([f"Page {p}" for p in pages_cited])
        top_snippet = context_chunks[0].content[:250].replace("\n", " ")
        
        return (
            f"Based on the document ({pages_str}), here is the relevant analysis regarding '{question}':\n\n"
            f"The document states: \"{top_snippet}...\". "
            f"According to Section '{context_chunks[0].section or 'Standard Terms'}', this provision governs "
            f"the contractual obligations and operational constraints specified by the parties."
        )
