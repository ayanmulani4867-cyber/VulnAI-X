import pytest
from app.models import ResearchJob
from app.worker.worker import AutonomousWorker
from app.config import settings

def test_job_creation_authorized(client, auth_headers, sample_program_and_scope):
    program, _ = sample_program_and_scope
    resp = client.post(
        "/api/jobs",
        json={
            "program_id": program.id,
            "target": "https://accounts.google.com",
            "module_type": "web"
        },
        headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["target"] == "https://accounts.google.com"

def test_job_creation_out_of_scope_forbidden(client, auth_headers, sample_program_and_scope):
    program, _ = sample_program_and_scope
    resp = client.post(
        "/api/jobs",
        json={
            "program_id": program.id,
            "target": "https://unauthorized-domain.com",
            "module_type": "web"
        },
        headers=auth_headers
    )
    assert resp.status_code == 403
    assert "Scope Authorization Check Failed" in resp.json()["detail"]

def test_job_cancellation(client, auth_headers, sample_program_and_scope):
    program, _ = sample_program_and_scope
    create_resp = client.post(
        "/api/jobs",
        json={
            "program_id": program.id,
            "target": "https://support.google.com",
            "module_type": "web"
        },
        headers=auth_headers
    )
    job_id = create_resp.json()["id"]

    cancel_resp = client.post(f"/api/jobs/{job_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200

    get_resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert get_resp.json()["status"] == "cancelled"

def test_emergency_stop_mechanism(client, auth_headers, sample_program_and_scope):
    program, _ = sample_program_and_scope
    
    # 1. Trigger emergency stop
    stop_resp = client.post(
        "/api/settings/emergency-stop",
        json={"reason": "Audit Test Emergency Stop"},
        headers=auth_headers
    )
    assert stop_resp.status_code == 200
    assert stop_resp.json()["emergency_stop"] is True

    # 2. Attempt to create a job - must be rejected
    fail_job = client.post(
        "/api/jobs",
        json={
            "program_id": program.id,
            "target": "https://admin.google.com",
            "module_type": "web"
        },
        headers=auth_headers
    )
    assert fail_job.status_code == 400
    assert "Emergency Stop is currently active" in fail_job.json()["detail"]

    # 3. Reset emergency stop
    reset_resp = client.post("/api/settings/emergency-stop/reset", headers=auth_headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["emergency_stop"] is False

def test_worker_startup_recovery(db, sample_program_and_scope):
    program, scope = sample_program_and_scope
    
    # Create an interrupted running job
    stuck_job = ResearchJob(
        program_id=program.id,
        scope_id=scope.id,
        title="Interrupted Job",
        target="https://drive.google.com",
        module_type="web",
        status="running",
        retry_count=0,
        max_retries=3
    )
    db.add(stuck_job)
    db.commit()

    # Instantiate worker with test db session and run recovery
    worker = AutonomousWorker(worker_id="test-recovery-worker", db=db)
    worker.recover_unfinished_jobs()

    db.refresh(stuck_job)
    assert stuck_job.status == "queued"
    assert stuck_job.retry_count == 1
    assert "Re-queued after worker recovery" in stuck_job.error_message
