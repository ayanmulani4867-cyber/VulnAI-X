from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NotificationLog, AuditEvent, ResearchJob
from app.schemas import EmergencyStopRequest, EmailTestRequest
from app.security.auth import get_current_active_user, require_roles
from app.notifications.email_service import EmailService
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["Settings & Safety"])

class SMTPConfigUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    notification_email_to: Optional[str] = None
    smtp_tls: Optional[bool] = True

@router.get("/config")
def get_current_config(current_user = Depends(get_current_active_user)):
    return {
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "emergency_stop": settings.EMERGENCY_STOP,
        "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_FROM),
        "smtp_host": settings.SMTP_HOST or "Not configured",
        "smtp_port": settings.SMTP_PORT,
        "smtp_from": settings.SMTP_FROM or "Not configured",
        "notification_email_to": settings.NOTIFICATION_EMAIL_TO or "Not configured",
        "smtp_tls": settings.SMTP_TLS,
        "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
        "job_timeout_seconds": settings.JOB_TIMEOUT_SECONDS,
        "allow_private_lab_targets": settings.ALLOW_PRIVATE_LAB_TARGETS
    }

@router.post("/smtp")
def update_smtp_config(
    cfg: SMTPConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if cfg.smtp_host is not None:
        settings.SMTP_HOST = cfg.smtp_host
    if cfg.smtp_port is not None:
        settings.SMTP_PORT = cfg.smtp_port
    if cfg.smtp_user is not None:
        settings.SMTP_USER = cfg.smtp_user
    if cfg.smtp_password is not None:
        settings.SMTP_PASSWORD = cfg.smtp_password
    if cfg.smtp_from is not None:
        settings.SMTP_FROM = cfg.smtp_from
    if cfg.notification_email_to is not None:
        settings.NOTIFICATION_EMAIL_TO = cfg.notification_email_to
    if cfg.smtp_tls is not None:
        settings.SMTP_TLS = cfg.smtp_tls

    audit = AuditEvent(
        user_id=current_user.id,
        action="SMTP_CONFIG_UPDATE",
        resource_type="config",
        details="Updated SMTP email server configuration."
    )
    db.add(audit)
    db.commit()

    return {"message": "SMTP configuration updated successfully."}

@router.post("/test-email")
async def test_email_alert(
    req: EmailTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    email_service = EmailService(db)
    success, msg = await email_service.send_alert(
        event_type="test_alert",
        subject="[VulnAI X] Test Email Notification",
        body=f"This is a test notification from VulnAI X triggered by user '{current_user.username}'.\nSMTP connection is operational.",
        recipient=req.recipient
    )
    return {"success": success, "message": msg}

@router.get("/notifications")
def list_notification_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    logs = db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(limit).all()
    return logs

@router.post("/emergency-stop")
def trigger_emergency_stop(
    req: EmergencyStopRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    settings.EMERGENCY_STOP = True

    # Cancel all running and queued jobs
    active_jobs = db.query(ResearchJob).filter(ResearchJob.status.in_(["queued", "running"])).all()
    for job in active_jobs:
        job.cancellation_requested = True
        job.status = "cancelled"
        job.error_message = f"Emergency stop invoked: {req.reason}"

    audit = AuditEvent(
        user_id=current_user.id,
        action="EMERGENCY_STOP_ACTIVATED",
        resource_type="system",
        details=f"Emergency stop activated by {current_user.username}. Reason: {req.reason}. Halted {len(active_jobs)} active jobs."
    )
    db.add(audit)
    db.commit()

    return {
        "emergency_stop": True,
        "message": f"Emergency stop activated. {len(active_jobs)} jobs halted.",
        "reason": req.reason
    }

@router.post("/emergency-stop/reset")
def reset_emergency_stop(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    settings.EMERGENCY_STOP = False

    audit = AuditEvent(
        user_id=current_user.id,
        action="EMERGENCY_STOP_RESET",
        resource_type="system",
        details=f"Emergency stop reset by {current_user.username}. Normal research operations restored."
    )
    db.add(audit)
    db.commit()

    return {"emergency_stop": False, "message": "Emergency stop cleared. System operational."}
