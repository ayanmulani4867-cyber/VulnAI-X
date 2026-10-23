from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ResearchJob, Finding, ScopeEntry, WorkerHeartbeat, AuditEvent
from app.schemas import DashboardStats
from app.security.auth import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    total_jobs = db.query(ResearchJob).count()
    running_jobs = db.query(ResearchJob).filter(ResearchJob.status == "running").count()
    
    potential_vulns = db.query(Finding).filter(Finding.status.in_(["Detected", "Needs Investigation", "Verification Pending"])).count()
    verified_findings = db.query(Finding).filter(Finding.status == "Verified in Authorized Environment").count()
    false_positives = db.query(Finding).filter(Finding.status == "False Positive").count()
    
    crit_high = db.query(Finding).filter(
        Finding.severity.in_(["Critical", "High"]),
        Finding.status != "False Positive"
    ).count()

    active_scopes = db.query(ScopeEntry).filter(ScopeEntry.status == "active").count()

    # Worker health check: heartbeat within last 30 seconds
    thirty_secs_ago = datetime.utcnow() - timedelta(seconds=30)
    recent_worker = db.query(WorkerHeartbeat).filter(
        WorkerHeartbeat.last_heartbeat >= thirty_secs_ago,
        WorkerHeartbeat.status.in_(["healthy", "busy"])
    ).first()

    if settings.EMERGENCY_STOP:
        worker_health = "Emergency Stopped"
    elif recent_worker:
        worker_health = "Online & Healthy"
    else:
        worker_health = "Idle / Offline"

    # Last scheduled run
    last_run_job = db.query(ResearchJob).filter(
        ResearchJob.is_scheduled == True,
        ResearchJob.status == "completed"
    ).order_by(ResearchJob.completed_at.desc()).first()
    
    last_scheduled_run = last_run_job.completed_at if last_run_job else None

    # Recent activity
    recent_events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(8).all()
    activity_list = []
    for ev in recent_events:
        activity_list.append({
            "id": ev.id,
            "action": ev.action,
            "resource": ev.resource_type,
            "details": ev.details or "",
            "timestamp": ev.timestamp.isoformat()
        })

    return DashboardStats(
        total_jobs=total_jobs,
        running_jobs=running_jobs,
        potential_vulnerabilities=potential_vulns,
        verified_findings=verified_findings,
        false_positives=false_positives,
        critical_and_high=crit_high,
        worker_health=worker_health,
        last_scheduled_run=last_scheduled_run,
        active_scopes_count=active_scopes,
        recent_activity=activity_list
    )
