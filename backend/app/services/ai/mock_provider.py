import re
import uuid
from datetime import datetime, timezone
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

    async def compare_documents(
        self,
        doc1_id: str,
        doc1_name: str,
        doc1_text: str,
        doc1_audit: Optional[Any],
        doc2_id: str,
        doc2_name: str,
        doc2_text: str,
        doc2_audit: Optional[Any],
        doc_type: Any
    ) -> Any:
        from app.models.comparison import (
            ComparativeAuditResult, 
            RiskDelta, 
            ClauseDiff, 
            MetricComparison, 
            DiffChangeType, 
            RiskImpactType
        )
        from app.models.document import DocumentType

        # Determine scores from audits if available
        d1_score = 32
        d2_score = 78
        d1_level = RiskLevel.LOW
        d2_level = RiskLevel.HIGH

        if doc1_audit:
            if hasattr(doc1_audit, 'legal_audit') and doc1_audit.legal_audit:
                d1_score = doc1_audit.legal_audit.overall_risk_score
                d1_level = doc1_audit.legal_audit.overall_risk_level
            elif hasattr(doc1_audit, 'financial_audit') and doc1_audit.financial_audit:
                d1_score = doc1_audit.financial_audit.overall_risk_score
                d1_level = doc1_audit.financial_audit.overall_risk_level

        if doc2_audit:
            if hasattr(doc2_audit, 'legal_audit') and doc2_audit.legal_audit:
                d2_score = doc2_audit.legal_audit.overall_risk_score
                d2_level = doc2_audit.legal_audit.overall_risk_level
            elif hasattr(doc2_audit, 'financial_audit') and doc2_audit.financial_audit:
                d2_score = doc2_audit.financial_audit.overall_risk_score
                d2_level = doc2_audit.financial_audit.overall_risk_level

        # If identical text/audits, make delta zero
        if doc1_id == doc2_id or doc1_text.strip() == doc2_text.strip():
            d2_score = d1_score
            d2_level = d1_level

        score_delta = d2_score - d1_score
        if score_delta >= 20:
            verdict = "SIGNIFICANT_RISK_INCREASE"
            summary_text = (
                f"Comparative audit detects a substantial escalation in legal and operational exposure (+{score_delta} risk points). "
                f"Revision '{doc2_name}' weakens protective covenants and substantially shifts liability."
            )
        elif score_delta > 5:
            verdict = "MODERATE_RISK_INCREASE"
            summary_text = f"Revision '{doc2_name}' increases commercial exposure (+{score_delta} risk points) with several unfavorable modifications."
        elif score_delta < -5:
            verdict = "RISK_DECREASED"
            summary_text = f"Revision '{doc2_name}' reflects an improved risk profile ({score_delta} risk points) with stronger protective guardrails."
        else:
            verdict = "NEUTRAL"
            summary_text = f"Documents exhibit an equivalent risk posture with minor or stylistic variances (delta: {score_delta})."

        risk_delta = RiskDelta(
            doc1_score=d1_score,
            doc2_score=d2_score,
            score_delta=score_delta,
            doc1_level=d1_level,
            doc2_level=d2_level,
            verdict=verdict,
            summary=summary_text
        )

        clause_diffs: List[ClauseDiff] = []
        metric_comparisons: List[MetricComparison] = []

        is_financial = (doc_type == DocumentType.FINANCIAL) or ("balance sheet" in doc1_text.lower() and "balance sheet" in doc2_text.lower())

        if is_financial:
            clause_diffs = [
                ClauseDiff(
                    category="Auditor Opinion & Independence",
                    doc1_clause="Unqualified / Clean Opinion under U.S. GAAP standards.",
                    doc2_clause="Qualified Opinion due to valuation uncertainty in inventory & foreign operations.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.CRITICAL_ESCALATION,
                    analysis="Audit opinion was downgraded from Unqualified to Qualified, indicating material non-compliance or valuation uncertainty."
                ),
                ClauseDiff(
                    category="Debt Covenants & Leverage",
                    doc1_clause="Debt-to-Equity: 0.27x ($32.0M Long-Term Debt)",
                    doc2_clause="Debt-to-Equity: 0.85x ($98.5M Long-Term Debt; Senior Secured Notes)",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.ADVERSE,
                    analysis="Significant debt accumulation triples leverage ratio, tightening headroom against solvency covenants."
                ),
                ClauseDiff(
                    category="Contingent Litigation Reserves",
                    doc1_clause="Accrued reserve of $1.8M for patent assertion and tax reviews.",
                    doc2_clause="Expanded legal proceedings reserve of $12.5M for class action litigation.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.ADVERSE,
                    analysis="Litigation reserve increased sevenfold, representing substantial near-term cash drain risk."
                )
            ]
            metric_comparisons = [
                MetricComparison(
                    metric_name="Gross Margin",
                    doc1_value="74.2%",
                    doc2_value="62.1%",
                    change_summary="Margin contracted by 12.1% due to elevated cloud hosting and COGS inflation.",
                    is_risk_increase=True
                ),
                MetricComparison(
                    metric_name="Operating Margin",
                    doc1_value="14.7%",
                    doc2_value="4.8%",
                    change_summary="Compressed operating margin nearing break-even threshold.",
                    is_risk_increase=True
                ),
                MetricComparison(
                    metric_name="Current Ratio (Liquidity)",
                    doc1_value="2.72x",
                    doc2_value="1.45x",
                    change_summary="Working capital buffer narrowed from robust 2.72x to 1.45x.",
                    is_risk_increase=True
                )
            ]
            takeaways = [
                "Overall financial stability weakened primarily due to aggressive debt expansion and litigation exposure.",
                "Auditor qualification requires immediate review by Audit Committee prior to executive sign-off.",
                "Operating margin compression suggests pricing pressure or unabsorbed capacity costs."
            ]
            strategies = [
                "Seek waiver or covenant modification from senior lenders before debt maturity.",
                "Conduct audit reconciliation on foreign inventory valuation to resolve auditor qualification.",
                "Ring-fence IP litigation exposure with specialized indemnity insurance."
            ]
        else:
            clause_diffs = [
                ClauseDiff(
                    category="Limitation of Liability",
                    doc1_clause="Liability capped at fees paid in preceding 12 months (maximum $50,000 USD). Mutual exclusion of consequential damages.",
                    doc2_clause="Neither party's liability under this Agreement shall be subject to any financial ceiling or monetary cap. Uncapped liability applies to all breaches.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.CRITICAL_ESCALATION,
                    analysis="Revision Document 2 deletes the monetary cap entirely. This exposes the enterprise to catastrophic, open-ended damages with no financial backstop."
                ),
                ClauseDiff(
                    category="Termination for Convenience & Notice",
                    doc1_clause="Either party may terminate without cause upon sixty (60) days prior written notice.",
                    doc2_clause="Customer may terminate at any time upon seven (7) days written notice. Vendor possesses no termination for convenience rights.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.ADVERSE,
                    analysis="Termination notice shortened from 60 days to 7 days and converted into a completely one-sided unilateral prerogative against the vendor."
                ),
                ClauseDiff(
                    category="Indemnification Scope",
                    doc1_clause="Mutual reciprocal indemnification for gross negligence and willful misconduct.",
                    doc2_clause="Vendor shall defend, indemnify, and hold harmless Customer from any and all third-party claims, costs, or investigations arising directly or indirectly.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.ADVERSE,
                    analysis="Reciprocity stripped away; indemnity obligation broadened to indirect claims without requirement of proven negligence or fault."
                ),
                ClauseDiff(
                    category="Governing Law & Dispute Forum",
                    doc1_clause="Governed by the State of Delaware; federal and state courts in New Castle County.",
                    doc2_clause="Governed by English Law; mandatory binding arbitration under LCIA rules seated in London, UK.",
                    change_type=DiffChangeType.MODIFIED,
                    risk_impact=RiskImpactType.NEUTRAL,
                    analysis="Forum moved from domestic court litigation to international commercial arbitration. Increases cross-border arbitration costs."
                ),
                ClauseDiff(
                    category="Service Level Agreement & Liquidated Damages",
                    doc1_clause="99.5% service uptime commitment with standard service credit remedy.",
                    doc2_clause="99.99% uptime commitment with mandatory liquidated damages of $10,000 per downtime hour payable in cash within 15 days.",
                    change_type=DiffChangeType.ADDED,
                    risk_impact=RiskImpactType.CRITICAL_ESCALATION,
                    analysis="Liquidated damages clause introduced, replacing standard credits with direct cash penalties that bypass customary damage mitigation."
                )
            ]
            metric_comparisons = [
                MetricComparison(
                    metric_name="Liability Monetary Cap",
                    doc1_value="$50,000 (12-Mo Fees)",
                    doc2_value="Uncapped (Unlimited)",
                    change_summary="Financial ceiling completely removed.",
                    is_risk_increase=True
                ),
                MetricComparison(
                    metric_name="Termination Notice Period",
                    doc1_value="60 Days (Mutual)",
                    doc2_value="7 Days (Unilateral)",
                    change_summary="Runway reduced by 88% and made unilateral.",
                    is_risk_increase=True
                ),
                MetricComparison(
                    metric_name="SLA Downtime Penalty",
                    doc1_value="Service Credits",
                    doc2_value="$10,000/hr Cash Penalty",
                    change_summary="Direct monetary liability introduced for minor outages.",
                    is_risk_increase=True
                )
            ]
            takeaways = [
                "Counterparty's redline introduces high-severity commercial risks by eliminating the liability ceiling.",
                "Unilateral 7-day termination creates operational instability and unhedged resource commitments.",
                "Cash liquidated damages on SLA metrics create an unacceptable financial exposure point."
            ]
            strategies = [
                "Strict Counter-Proposal: Reject uncapped liability; propose a compromise cap at 2x annual contract value ($100k).",
                "Restore a mutual 30-day minimum termination notice for both parties to prevent abrupt cancellations.",
                "Strike the $10,000/hr cash penalty; replace with tiered recurring service credits capped at 20% of monthly billing."
            ]

        comparison_id = f"cmp-{uuid.uuid4().hex[:10]}"
        return ComparativeAuditResult(
            id=comparison_id,
            doc1_id=doc1_id,
            doc1_name=doc1_name,
            doc2_id=doc2_id,
            doc2_name=doc2_name,
            doc_type=doc_type or DocumentType.LEGAL,
            completed_at=datetime.now(timezone.utc),
            provider_used=self.provider_name,
            model_used=self.model_name,
            risk_delta=risk_delta,
            executive_comparison=summary_text,
            clause_diffs=clause_diffs,
            metric_comparisons=metric_comparisons,
            key_takeaways=takeaways,
            renegotiation_strategy=strategies
        )
