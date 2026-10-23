from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import WorkerHeartbeat, ResearchJob
from app.schemas import SystemHealthResponse
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/api/health", response_model=SystemHealthResponse)
def health_check(db: Session = Depends(get_db)):
    # 1. DB ping
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. Worker heartbeat
    thirty_secs_ago = datetime.utcnow() - timedelta(seconds=30)
    worker = db.query(WorkerHeartbeat).filter(
        WorkerHeartbeat.last_heartbeat >= thirty_secs_ago
    ).order_by(WorkerHeartbeat.last_heartbeat.desc()).first()

    worker_status = "healthy" if worker and worker.status != "stopped" else "offline"
    active_jobs = db.query(ResearchJob).filter(ResearchJob.status == "running").count()

    overall_status = "healthy"
    if db_status != "healthy":
        overall_status = "degraded"
    if settings.EMERGENCY_STOP:
        overall_status = "emergency_stopped"

    return SystemHealthResponse(
        status=overall_status,
        database=db_status,
        worker_status=worker_status,
        last_heartbeat=worker.last_heartbeat if worker else None,
        active_jobs=active_jobs,
        emergency_stop=settings.EMERGENCY_STOP,
        version=settings.APP_VERSION
    )
