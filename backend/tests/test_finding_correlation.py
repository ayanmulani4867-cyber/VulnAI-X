import pytest
from app.agents.orchestrator import MultiAgentOrchestrator
from app.models import Finding, ResearchJob

def test_correlation_and_deduplication(db, sample_program_and_scope):
    program, scope = sample_program_and_scope
    orchestrator = MultiAgentOrchestrator(db)
    job = ResearchJob(
        program_id=program.id,
        target="https://example.google.com",
        title="Deduplication Test",
        module_type="web"
    )

    observations = [
        {
            "title": "Missing Content-Security-Policy",
            "rule_id": "vulnai.headers.csp",
            "category": "Headers",
            "severity": "Medium",
            "confidence": "Certain",
            "evidence": "Observation 1: Header absent."
        },
        {
            "title": "Missing Content-Security-Policy",
            "rule_id": "vulnai.headers.csp",
            "category": "Headers",
            "severity": "Medium",
            "confidence": "Certain",
            "evidence": "Observation 2: Confirmed absent on re-check."
        }
    ]

    correlated = orchestrator._correlate_findings(job, observations)
    assert len(correlated) == 1
    assert "Observation 1" in correlated[0]["evidence"]
    assert "Observation 2" in correlated[0]["evidence"]

def test_verification_agent_states(db):
    orchestrator = MultiAgentOrchestrator(db)
    
    findings_to_verify = [
        {
            "title": "Certain with strong evidence",
            "confidence": "Certain",
            "evidence": "Valid HTTP 200 response with confirmed missing header token."
        },
        {
            "title": "High confidence observation",
            "confidence": "High",
            "evidence": "Heuristic match on export component in manifest."
        },
        {
            "title": "Weak or unverified observation",
            "confidence": "Low",
            "evidence": ""
        }
    ]

    verified = orchestrator._verify_findings(findings_to_verify)
    assert verified[0]["status"] == "Verified in Authorized Environment"
    assert verified[1]["status"] == "Needs Investigation"
    assert verified[2]["status"] == "Detected"

def test_update_finding_status(client, auth_headers, sample_program_and_scope, db):
    program, scope = sample_program_and_scope
    finding = Finding(
        program_id=program.id,
        title="Sample Finding",
        category="Web",
        severity="Medium",
        confidence="High",
        status="Detected",
        target="https://test.google.com",
        evidence_summary="Test evidence"
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)

    # Patch status to False Positive
    patch_resp = client.patch(
        f"/api/findings/{finding.id}",
        json={"status": "False Positive", "false_positive_reason": "Intentionally public test environment."},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "False Positive"
    assert patch_resp.json()["false_positive_reason"] == "Intentionally public test environment."
