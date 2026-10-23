from typing import List, Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ResearchJob, JobAttempt, AuditEvent
from app.schemas import ResearchJobCreate, ResearchJobResponse, JobAttemptResponse
from app.security.auth import get_current_active_user, require_roles
from app.security.scope_guard import validate_target_scope
from app.agents.orchestrator import MultiAgentOrchestrator
from app.config import settings

router = APIRouter(prefix="/api/jobs", tags=["Research Jobs"])

@router.get("", response_model=List[ResearchJobResponse])
def list_jobs(
    status_filter: Optional[str] = None,
    program_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(ResearchJob)
    if status_filter:
        query = query.filter(ResearchJob.status == status_filter)
    if program_id:
        query = query.filter(ResearchJob.program_id == program_id)
        
    jobs = query.order_by(ResearchJob.created_at.desc()).all()
    res = []
    for j in jobs:
        j_dict = {
            "id": j.id,
            "program_id": j.program_id,
            "scope_id": j.scope_id,
            "title": j.title,
            "target": j.target,
            "module_type": j.module_type,
            "status": j.status,
            "priority": j.priority,
            "retry_count": j.retry_count,
            "max_retries": j.max_retries,
            "error_message": j.error_message,
            "cancellation_requested": j.cancellation_requested,
            "is_scheduled": j.is_scheduled,
            "cron_expression": j.cron_expression,
            "started_at": j.started_at,
            "completed_at": j.completed_at,
            "created_at": j.created_at,
            "findings_count": len(j.findings)
        }
        res.append(j_dict)
    return res

@router.post("", response_model=ResearchJobResponse)
def create_job(
    job_in: ResearchJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    if settings.EMERGENCY_STOP:
        raise HTTPException(
            status_code=400,
            detail="Emergency Stop is currently active. Job creation is prohibited."
        )

    # 1. Mandatory Scope Validation (Fail-Closed)
    is_authorized, msg, scope = validate_target_scope(
        db, job_in.program_id, job_in.target, requested_method="passive"
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Scope Authorization Check Failed: {msg}"
        )

    title = job_in.title or f"Research [{job_in.module_type.upper()}]: {job_in.target}"

    job = ResearchJob(
        program_id=job_in.program_id,
        scope_id=scope.id if scope else None,
        title=title,
        target=job_in.target,
        module_type=job_in.module_type,
        status="queued",
        is_scheduled=job_in.is_scheduled,
        cron_expression=job_in.cron_expression,
        created_by=current_user.username
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    audit = AuditEvent(
        user_id=current_user.id,
        action="JOB_CREATE",
        resource_type="job",
        resource_id=job.id,
        details=f"Queued job '{job.title}' targeting '{job.target}' under scope '{scope.authorization_reference}'."
    )
    db.add(audit)
    db.commit()

    return job

@router.get("/{job_id}", response_model=ResearchJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")
    
    return {
        "id": job.id,
        "program_id": job.program_id,
        "scope_id": job.scope_id,
        "title": job.title,
        "target": job.target,
        "module_type": job.module_type,
        "status": job.status,
        "priority": job.priority,
        "retry_count": job.retry_count,
        "max_retries": job.max_retries,
        "error_message": job.error_message,
        "cancellation_requested": job.cancellation_requested,
        "is_scheduled": job.is_scheduled,
        "cron_expression": job.cron_expression,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "findings_count": len(job.findings)
    }

@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status in ("completed", "failed", "cancelled"):
        return {"message": f"Job is already {job.status}."}

    job.cancellation_requested = True
    if job.status == "queued":
        job.status = "cancelled"

    db.commit()

    audit = AuditEvent(
        user_id=current_user.id,
        action="JOB_CANCEL",
        resource_type="job",
        resource_id=job.id,
        details=f"Cancellation requested for job '{job.title}'."
    )
    db.add(audit)
    db.commit()

    return {"message": "Job cancellation requested successfully."}

@router.post("/{job_id}/run-now")
async def run_job_now(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    """Executes a queued job directly using the orchestrator."""
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status == "running":
        raise HTTPException(status_code=400, detail="Job is already running.")

    orchestrator = MultiAgentOrchestrator(db)
    result = await orchestrator.execute_job(job_id)
    return result

@router.get("/{job_id}/attempts", response_model=List[JobAttemptResponse])
def get_job_attempts(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return db.query(JobAttempt).filter(JobAttempt.job_id == job_id).order_by(JobAttempt.attempt_number.asc()).all()
