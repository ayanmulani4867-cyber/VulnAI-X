import os
import pytest
from app.reporting.report_generator import ReportGenerator
from app.models import ResearchJob, Finding
from app.config import settings

def test_json_and_pdf_report_generation(sample_program_and_scope, db):
    program, scope = sample_program_and_scope

    job = ResearchJob(
        program_id=program.id,
        scope_id=scope.id,
        title="Automated Test Job",
        target="https://bughunters.google.com",
        module_type="web",
        status="completed"
    )
    db.add(job)
    db.flush()

    finding = Finding(
        job_id=job.id,
        program_id=program.id,
        scope_id=scope.id,
        title="Missing Strict-Transport-Security Header",
        category="Security Headers",
        severity="Medium",
        confidence="Certain",
        status="Verified in Authorized Environment",
        target="https://bughunters.google.com",
        evidence_summary="HTTP response lacked HSTS directive.",
        remediation="Enable HSTS with max-age=31536000."
    )
    db.add(finding)
    db.commit()

    # 1. JSON Report
    json_data = ReportGenerator.generate_json_report(job, [finding], program)
    assert "vulnai_x_report" in json_data
    report = json_data["vulnai_x_report"]
    assert report["summary"]["total_findings"] == 1
    assert report["summary"]["verified_in_authorized_env"] == 1
    assert len(report["findings"]) == 1

    # 2. PDF Report
    pdf_path = os.path.join(settings.REPORTS_DIR, f"test_report_{job.id[:6]}.pdf")
    generated_path = ReportGenerator.generate_pdf_report(job, [finding], program, pdf_path)
    assert os.path.exists(generated_path)
    assert os.path.getsize(generated_path) > 1000 # Valid non-empty PDF binary
