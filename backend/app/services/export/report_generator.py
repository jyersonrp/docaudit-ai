import json
import io
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.security import escape_xml as xml_escape
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, 
    Paragraph, 
    Spacer, 
    Table, 
    TableStyle, 
    HRFlowable, 
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from app.models.audit import AuditResult, LegalContractAudit, FinancialReportAudit, CustomAudit
from app.models.document import DocumentMetadata

class ReportGenerator:
    @staticmethod
    def generate_markdown(audit: AuditResult, metadata: DocumentMetadata) -> str:
        lines = []
        lines.append(f"# DocAudit AI Executive Report")
        lines.append(f"**Document Name:** `{metadata.filename}`  ")
        lines.append(f"**Audit Type:** {audit.audit_type.value.upper()}  ")
        lines.append(f"**Audit Date:** {audit.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
        lines.append(f"**AI Engine:** `{audit.provider_used}` ({audit.model_used})  ")
        lines.append("\n---\n")

        # Specific audit body
        if audit.legal_audit:
            leg = audit.legal_audit
            lines.append(f"## 1. Executive Summary")
            lines.append(f"{leg.executive_summary}\n")
            lines.append(f"### Core Contract Parameters")
            lines.append(f"- **Parties:** {', '.join(leg.parties)}")
            lines.append(f"- **Effective Term:** {leg.effective_date or 'N/A'} to {leg.expiration_date or 'Indefinite'}")
            lines.append(f"- **Governing Law / Jurisdiction:** {leg.governing_law or 'N/A'} ({leg.jurisdiction or 'N/A'})")
            lines.append(f"- **Termination Notice:** {leg.termination_notice_period or 'N/A'}")
            lines.append(f"- **Liability Cap:** {leg.liability_cap or 'N/A'}")
            lines.append(f"- **Overall Risk Level:** **{leg.overall_risk_level.value}** ({leg.overall_risk_score}/100)\n")

            lines.append(f"## 2. Risk Matrix Breakdown")
            lines.append("| Dimension | Score | Level | Evaluation |")
            lines.append("| :--- | :---: | :---: | :--- |")
            for r in leg.risk_matrix:
                lines.append(f"| {r.dimension} | {r.score}/100 | {r.level.value} | {r.summary} |")
            lines.append("\n")

            lines.append(f"## 3. Key Findings & Actionable Recommendations")
            for f in leg.key_findings:
                lines.append(f"### [{f.severity.value}] {f.title} ({f.category})")
                if f.page_number:
                    lines.append(f"**Page:** {f.page_number}")
                if f.quote:
                    lines.append(f"> \"{f.quote}\"\n")
                lines.append(f"- **Description:** {f.description}")
                lines.append(f"- **Impact:** {f.impact}")
                lines.append(f"- **Recommendation:** {f.recommendation}\n")

            lines.append(f"## 4. Compliance Checklist")
            for item, passed in leg.compliance_checklist.items():
                status = "PASS [x]" if passed else "ATTENTION [ ]"
                lines.append(f"- {status} {item}")

        elif audit.financial_audit:
            fin = audit.financial_audit
            lines.append(f"## 1. Financial Health Executive Summary")
            lines.append(f"{fin.executive_summary}\n")
            lines.append(f"### Key Financial Metrics")
            lines.append(f"- **Company:** {fin.company_name or 'N/A'}")
            lines.append(f"- **Period:** {fin.reporting_period or 'N/A'}")
            lines.append(f"- **Revenue:** {fin.total_revenue or 'N/A'} ({fin.currency})")
            lines.append(f"- **Net Income:** {fin.net_income or 'N/A'}")
            lines.append(f"- **Operating Margin:** {fin.operating_margin or 'N/A'}")
            lines.append(f"- **Debt-to-Equity:** {fin.debt_to_equity or 'N/A'}")
            lines.append(f"- **Auditor Opinion:** {fin.auditor_opinion}")
            lines.append(f"- **Overall Risk Level:** **{fin.overall_risk_level.value}** ({fin.overall_risk_score}/100)\n")

            lines.append(f"## 2. Risk Matrix Breakdown")
            lines.append("| Dimension | Score | Level | Evaluation |")
            lines.append("| :--- | :---: | :---: | :--- |")
            for r in fin.risk_matrix:
                lines.append(f"| {r.dimension} | {r.score}/100 | {r.level.value} | {r.summary} |")
            lines.append("\n")

            lines.append(f"## 3. Findings & Disclosures")
            for f in fin.key_findings:
                lines.append(f"### [{f.severity.value}] {f.title} ({f.category})")
                lines.append(f"- **Analysis:** {f.description}")
                lines.append(f"- **Impact:** {f.impact}")
                lines.append(f"- **Recommendation:** {f.recommendation}\n")

            if fin.contingent_liabilities:
                lines.append("### Contingent Liabilities & Legal Exposures")
                for item in fin.contingent_liabilities:
                    lines.append(f"- {item}")
                lines.append("\n")

            if fin.fiscal_risks:
                lines.append("### Fiscal & Tax Exposures")
                for item in fin.fiscal_risks:
                    lines.append(f"- {item}")
                lines.append("\n")

            lines.append("## 4. Compliance & Accounting Standards Checklist")
            for item, passed in fin.compliance_checklist.items():
                status = "PASS [x]" if passed else "ATTENTION [ ]"
                lines.append(f"- {status} {item}")

        elif audit.custom_audit:
            cust = audit.custom_audit
            lines.append(f"## 1. Custom Audit Summary ({cust.audit_name})")
            lines.append(f"{cust.executive_summary}\n")
            lines.append(f"- **Overall Risk Level:** **{cust.overall_risk_level.value}** ({cust.overall_risk_score}/100)\n")
            lines.append(f"### Extracted Custom Fields")
            for k, v in cust.extracted_fields.items():
                lines.append(f"- **{k}:** {v}")
            lines.append("\n### Key Findings & Recommendations")
            for f in cust.key_findings:
                lines.append(f"### [{f.severity.value}] {f.title} ({f.category})")
                lines.append(f"- **Description:** {f.description}")
                lines.append(f"- **Impact:** {f.impact}")
                lines.append(f"- **Recommendation:** {f.recommendation}\n")

            if cust.compliance_checklist:
                lines.append("## 4. Custom Compliance Checklist")
                for item, passed in cust.compliance_checklist.items():
                    status = "PASS [x]" if passed else "ATTENTION [ ]"
                    lines.append(f"- {status} {item}")

        return "\n".join(lines)

    @staticmethod
    def generate_json(audit: AuditResult, metadata: DocumentMetadata) -> Dict[str, Any]:
        return {
            "metadata": metadata.model_dump(mode="json"),
            "audit_result": audit.model_dump(mode="json")
        }

    @staticmethod
    def generate_pdf(audit: AuditResult, metadata: DocumentMetadata) -> bytes:
        """
        Generates a publication-grade executive audit report in PDF format.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom palette
        brand_dark = colors.HexColor("#0F172A")
        brand_blue = colors.HexColor("#2563EB")
        text_dark = colors.HexColor("#1E293B")
        text_muted = colors.HexColor("#64748B")
        bg_light = colors.HexColor("#F8FAFC")
        border_color = colors.HexColor("#E2E8F0")

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=brand_dark,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=text_muted,
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=brand_dark,
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=text_dark,
            spaceAfter=6
        )

        badge_style = ParagraphStyle(
            "BadgeStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER
        )

        story = []

        # Header Title
        story.append(Paragraph("DocAudit AI &bull; Executive Audit Report", title_style))
        story.append(Paragraph(
            f"Document: <b>{xml_escape(metadata.filename)}</b> &nbsp;|&nbsp; "
            f"Generated: {audit.completed_at.strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp; "
            f"Engine: {xml_escape(audit.provider_used.upper())} ({xml_escape(audit.model_used)})",
            subtitle_style
        ))
        story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=0, spaceAfter=12))

        # Risk Banner
        overall_score = 0
        overall_level = "LOW"
        if audit.legal_audit:
            overall_score = audit.legal_audit.overall_risk_score
            overall_level = audit.legal_audit.overall_risk_level.value
            exec_summary = audit.legal_audit.executive_summary
        elif audit.financial_audit:
            overall_score = audit.financial_audit.overall_risk_score
            overall_level = audit.financial_audit.overall_risk_level.value
            exec_summary = audit.financial_audit.executive_summary
        elif audit.custom_audit:
            overall_score = audit.custom_audit.overall_risk_score
            overall_level = audit.custom_audit.overall_risk_level.value
            exec_summary = audit.custom_audit.executive_summary
        else:
            exec_summary = "Audit data pending."

        # Badge color based on risk
        badge_text = colors.HexColor("#166534") if overall_score < 40 else (colors.HexColor("#92400E") if overall_score < 70 else colors.HexColor("#991B1B"))

        risk_table_data = [
            [
                Paragraph("<b>AUDIT CLASSIFICATION</b>", ParagraphStyle("H", parent=body_style, textColor=text_muted, fontSize=8)),
                Paragraph("<b>GLOBAL RISK SCORE</b>", ParagraphStyle("H", parent=body_style, textColor=text_muted, fontSize=8, alignment=TA_CENTER)),
                Paragraph("<b>OVERALL RISK TIER</b>", ParagraphStyle("H", parent=body_style, textColor=text_muted, fontSize=8, alignment=TA_CENTER))
            ],
            [
                Paragraph(f"<b>{xml_escape(audit.audit_type.value.upper())} AUDIT</b>", body_style),
                Paragraph(f"<b>{overall_score} / 100</b>", badge_style),
                Paragraph(f"<b>{xml_escape(overall_level)}</b>", ParagraphStyle("B", parent=badge_style, textColor=badge_text))
            ]
        ]
        t_banner = Table(risk_table_data, colWidths=[200, 170, 170])
        t_banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_light),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_banner)
        story.append(Spacer(1, 10))

        # Executive Summary Section
        story.append(Paragraph("1. Executive Briefing", h2_style))
        story.append(Paragraph(xml_escape(exec_summary), body_style))
        story.append(Spacer(1, 8))

        # Key Parameters & Metrics Section
        if audit.legal_audit:
            leg = audit.legal_audit
            story.append(Paragraph("2. Key Contractual Parameters", h2_style))
            param_data = [
                [Paragraph("<b>Contract Parameter</b>", body_style), Paragraph("<b>Identified Specification</b>", body_style)],
                [Paragraph("Contracting Parties", body_style), Paragraph(xml_escape(", ".join(leg.parties) if leg.parties else "N/A"), body_style)],
                [Paragraph("Governing Law & Venue", body_style), Paragraph(xml_escape(f"{leg.governing_law or 'N/A'} ({leg.jurisdiction or 'N/A'})"), body_style)],
                [Paragraph("Effective Term", body_style), Paragraph(xml_escape(f"{leg.effective_date or 'N/A'} to {leg.expiration_date or 'Indefinite'}"), body_style)],
                [Paragraph("Termination Notice", body_style), Paragraph(xml_escape(leg.termination_notice_period or "N/A"), body_style)],
                [Paragraph("Liability Cap", body_style), Paragraph(xml_escape(leg.liability_cap or "N/A"), body_style)],
                [Paragraph("Indemnification Scope", body_style), Paragraph(xml_escape(leg.indemnification_scope or "Standard"), body_style)],
            ]
            t_params = Table(param_data, colWidths=[180, 360])
            t_params.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_light),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_params)
            story.append(Spacer(1, 8))

        elif audit.financial_audit:
            fin = audit.financial_audit
            story.append(Paragraph("2. Audited Financial Statements Metrics", h2_style))
            fin_data = [
                [Paragraph("<b>Financial Metric</b>", body_style), Paragraph("<b>Value / Reported Position</b>", body_style)],
                [Paragraph("Audited Entity", body_style), Paragraph(xml_escape(f"{fin.company_name or 'N/A'} ({fin.reporting_period or 'N/A'})"), body_style)],
                [Paragraph("Total Revenue", body_style), Paragraph(xml_escape(f"{fin.total_revenue or 'N/A'} {fin.currency}"), body_style)],
                [Paragraph("Net Income & Operating Margin", body_style), Paragraph(xml_escape(f"{fin.net_income or 'N/A'} (Margin: {fin.operating_margin or 'N/A'})"), body_style)],
                [Paragraph("Debt-to-Equity Ratio", body_style), Paragraph(xml_escape(fin.debt_to_equity or "N/A"), body_style)],
                [Paragraph("Independent Auditor Opinion", body_style), Paragraph(xml_escape(fin.auditor_opinion or "Unqualified"), body_style)],
            ]
            t_fin = Table(fin_data, colWidths=[180, 360])
            t_fin.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_light),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_fin)
            story.append(Spacer(1, 8))

        elif audit.custom_audit and audit.custom_audit.extracted_fields:
            cust = audit.custom_audit
            story.append(Paragraph(f"2. Extracted Criteria & Rules ({xml_escape(cust.audit_name)})", h2_style))
            cust_rows = [
                [Paragraph("<b>Criterion / Property</b>", body_style), Paragraph("<b>Extracted Value</b>", body_style)]
            ]
            for k, v in cust.extracted_fields.items():
                cust_rows.append([
                    Paragraph(xml_escape(str(k).replace('_', ' ').capitalize()), body_style),
                    Paragraph(xml_escape(str(v)), body_style)
                ])
            t_cust = Table(cust_rows, colWidths=[180, 360])
            t_cust.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_light),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_cust)
            story.append(Spacer(1, 8))

        # Risk Matrix Section
        risk_matrix = []
        if audit.legal_audit:
            risk_matrix = audit.legal_audit.risk_matrix
        elif audit.financial_audit:
            risk_matrix = audit.financial_audit.risk_matrix
        elif audit.custom_audit:
            risk_matrix = audit.custom_audit.risk_matrix

        if risk_matrix:
            story.append(Paragraph("3. Risk Dimensions Matrix", h2_style))
            matrix_rows = [
                [
                    Paragraph("<b>Risk Dimension</b>", body_style),
                    Paragraph("<b>Score</b>", ParagraphStyle("C", parent=body_style, alignment=TA_CENTER)),
                    Paragraph("<b>Tier</b>", ParagraphStyle("C", parent=body_style, alignment=TA_CENTER)),
                    Paragraph("<b>Evaluation & Rationale</b>", body_style)
                ]
            ]
            for r in risk_matrix:
                matrix_rows.append([
                    Paragraph(xml_escape(r.dimension), body_style),
                    Paragraph(f"{r.score}/100", ParagraphStyle("C", parent=body_style, alignment=TA_CENTER)),
                    Paragraph(xml_escape(r.level.value), ParagraphStyle("C", parent=body_style, alignment=TA_CENTER)),
                    Paragraph(xml_escape(r.summary), body_style)
                ])

            t_matrix = Table(matrix_rows, colWidths=[130, 60, 70, 280])
            t_matrix.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_light),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_matrix)
            story.append(Spacer(1, 10))

        # Detailed Findings Section
        findings = []
        if audit.legal_audit:
            findings = audit.legal_audit.key_findings
        elif audit.financial_audit:
            findings = audit.financial_audit.key_findings
        elif audit.custom_audit:
            findings = audit.custom_audit.key_findings

        if findings:
            story.append(Paragraph("4. Key Findings & Remediations", h2_style))
            for f in findings:
                sev_color = colors.HexColor("#DC2626") if f.severity.value in ["HIGH", "CRITICAL"] else (colors.HexColor("#D97706") if f.severity.value == "MEDIUM" else colors.HexColor("#16A34A"))
                f_data = [
                    [
                        Paragraph(f"<b>[{xml_escape(f.severity.value)}] {xml_escape(f.title)}</b> &nbsp;|&nbsp; <i>{xml_escape(f.category)}</i>", ParagraphStyle("FH", parent=body_style, textColor=sev_color))
                    ],
                    [
                        Paragraph(f"<b>Description:</b> {xml_escape(f.description)}", body_style)
                    ],
                    [
                        Paragraph(f"<b>Impact:</b> {xml_escape(f.impact)}", body_style)
                    ],
                    [
                        Paragraph(f"<b>Recommendation:</b> {xml_escape(f.recommendation)}", ParagraphStyle("FR", parent=body_style, textColor=brand_blue))
                    ]
                ]
                if f.quote:
                    f_data.append([
                        Paragraph(f"<b>Document Excerpt (Page {f.page_number or 'N/A'}):</b> <i>\"{xml_escape(f.quote)}\"</i>", ParagraphStyle("FQ", parent=body_style, textColor=text_muted))
                    ])

                t_f = Table(f_data, colWidths=[540])
                t_f.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(t_f)
                story.append(Spacer(1, 6))

        # Compliance Checklist
        checklist = {}
        if audit.legal_audit:
            checklist = audit.legal_audit.compliance_checklist
        elif audit.financial_audit:
            checklist = audit.financial_audit.compliance_checklist
        elif audit.custom_audit:
            checklist = audit.custom_audit.compliance_checklist

        if checklist:
            story.append(Spacer(1, 6))
            story.append(Paragraph("5. Regulatory & Operational Checklist", h2_style))
            chk_rows = [
                [Paragraph("<b>Standard / Rule</b>", body_style), Paragraph("<b>Status</b>", ParagraphStyle("C", parent=body_style, alignment=TA_CENTER))]
            ]
            for rule_name, passed in checklist.items():
                status_txt = "PASSED" if passed else "ATTENTION REQUIRED"
                status_col = colors.HexColor("#166534") if passed else colors.HexColor("#DC2626")
                chk_rows.append([
                    Paragraph(xml_escape(rule_name), body_style),
                    Paragraph(f"<b>{status_txt}</b>", ParagraphStyle("CS", parent=body_style, alignment=TA_CENTER, textColor=status_col))
                ])

            t_chk = Table(chk_rows, colWidths=[420, 120])
            t_chk.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_light),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_chk)

        # Build document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
