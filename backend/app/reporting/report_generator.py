import os
import json
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models import ResearchJob, Finding, AuthorizedProgram
from app.config import settings

class ReportGenerator:
    @staticmethod
    def generate_json_report(job: ResearchJob, findings: List[Finding], program: AuthorizedProgram) -> Dict[str, Any]:
        """Generates a structured JSON security research report."""
        findings_data = []
        for f in findings:
            findings_data.append({
                "id": f.id,
                "title": f.title,
                "category": f.category,
                "severity": f.severity,
                "confidence": f.confidence,
                "status": f.status,
                "target": f.target,
                "evidence_summary": f.evidence_summary,
                "reproduction_steps": f.reproduction_steps,
                "impact": f.impact,
                "remediation": f.remediation,
                "tool_name": f.tool_name,
                "rule_id": f.rule_id,
                "first_detected_at": str(f.first_detected_at),
                "last_observed_at": str(f.last_observed_at)
            })

        return {
            "vulnai_x_report": {
                "generated_at": datetime.utcnow().isoformat(),
                "program": {
                    "id": program.id,
                    "name": program.name,
                    "organization": program.organization,
                    "policy_url": program.policy_url
                },
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "target": job.target,
                    "module_type": job.module_type,
                    "status": job.status,
                    "started_at": str(job.started_at),
                    "completed_at": str(job.completed_at)
                },
                "summary": {
                    "total_findings": len(findings),
                    "critical": sum(1 for f in findings if f.severity == "Critical"),
                    "high": sum(1 for f in findings if f.severity == "High"),
                    "medium": sum(1 for f in findings if f.severity == "Medium"),
                    "low": sum(1 for f in findings if f.severity == "Low"),
                    "informational": sum(1 for f in findings if f.severity == "Informational"),
                    "verified_in_authorized_env": sum(1 for f in findings if f.status == "Verified in Authorized Environment"),
                    "needs_investigation": sum(1 for f in findings if f.status == "Needs Investigation")
                },
                "findings": findings_data,
                "disclaimer": "This report contains drafts prepared for human review and authorized remediation. Not submitted to bug bounty programs automatically."
            }
        }

    @staticmethod
    def generate_pdf_report(job: ResearchJob, findings: List[Finding], program: AuthorizedProgram, output_path: str) -> str:
        """Generates a professional PDF research report using ReportLab."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        styles = getSampleStyleSheet()

        # Custom styling
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )
        sub_style = ParagraphStyle(
            'ReportSub',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'H2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4
        )

        elements = []

        # Header Title
        elements.append(Paragraph("VulnAI X — Security Research & Audit Report", title_style))
        elements.append(Paragraph(f"Authorized Program: <b>{program.name}</b> | Target: <b>{job.target}</b> | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

        # Executive Summary Box
        elements.append(Paragraph("1. Executive Summary", h2_style))
        crit_count = sum(1 for f in findings if f.severity == "Critical")
        high_count = sum(1 for f in findings if f.severity == "High")
        med_count = sum(1 for f in findings if f.severity == "Medium")
        low_count = sum(1 for f in findings if f.severity == "Low")
        info_count = sum(1 for f in findings if f.severity == "Informational")

        summary_data = [
            ["Severity", "Count", "Classification Policy"],
            ["Critical", str(crit_count), "Direct business impact or unauthorized remote access"],
            ["High", str(high_count), "High-risk vulnerability requiring immediate remediation"],
            ["Medium", str(med_count), "Moderate impact / requires specific preconditions"],
            ["Low", str(low_count), "Defense-in-depth or minor weakness"],
            ["Informational", str(info_count), "Security headers, fingerprinting, or policy observations"]
        ]

        summary_table = Table(summary_data, colWidths=[100, 70, 360])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # Detailed Findings Section
        elements.append(Paragraph("2. Correlated Findings & Evidence", h2_style))
        if not findings:
            elements.append(Paragraph("No vulnerabilities or policy deviations detected during this research execution.", body_style))
        else:
            for idx, f in enumerate(findings, 1):
                sev_color = '#DC2626' if f.severity == 'Critical' else '#EA580C' if f.severity == 'High' else '#D97706' if f.severity == 'Medium' else '#2563EB'
                elements.append(Paragraph(f"<b>{idx}. {f.title}</b>", ParagraphStyle('FTitle', parent=h2_style, fontSize=11, leading=15, textColor=colors.HexColor(sev_color))))
                
                f_info = [
                    ["Severity", f.severity, "Confidence", f.confidence],
                    ["Category", f.category, "Status", f.status],
                    ["Tool / Rule", f"{f.tool_name} / {f.rule_id}", "Target", f.target]
                ]
                f_table = Table(f_info, colWidths=[80, 180, 80, 190])
                f_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
                    ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F8FAFC')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                elements.append(f_table)
                elements.append(Spacer(1, 4))
                
                elements.append(Paragraph(f"<b>Evidence:</b> {f.evidence_summary[:400]}", body_style))
                if f.remediation:
                    elements.append(Paragraph(f"<b>Recommended Remediation:</b> {f.remediation}", body_style))
                elements.append(Spacer(1, 8))

        # Human Review & Submission Notice
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        elements.append(Paragraph("<b>Notice:</b> This draft is generated by VulnAI X for human verification. Ensure reproduction steps comply with authorized program policy before external submission.", ParagraphStyle('Notice', parent=body_style, fontSize=8, textColor=colors.HexColor('#64748B'))))

        doc.build(elements)
        return output_path
