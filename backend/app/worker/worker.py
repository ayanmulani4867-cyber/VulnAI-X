import asyncio
import os
import sys
import time
import socket
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ResearchJob, JobAttempt, WorkerHeartbeat, ScopeEntry
from app.agents.orchestrator import MultiAgentOrchestrator
from app.config import settings

class AutonomousWorker:
    def __init__(self, worker_id: str = None, db: Optional[Session] = None):
        self.worker_id = worker_id or f"worker-{socket.gethostname()}-{os.getpid()}"
        self.running = False
        self.active_jobs = 0
        self._db = db

    def get_db(self) -> Session:
        if self._db is not None:
            return self._db
        return SessionLocal()

    async def start(self):
        """Starts worker process with crash recovery and polling loop."""
        self.running = True
        print(f"[*] VulnAI X Background Worker '{self.worker_id}' started.")
        
        # 1. Crash & Startup Recovery
        self.recover_unfinished_jobs()

        # 2. Main loop
        while self.running:
            try:
                # Update heartbeat
                self.record_heartbeat()

                if not settings.EMERGENCY_STOP:
                    # Pick next eligible queued job
                    await self.process_next_job()
                else:
                    print("[!] Emergency stop active. Worker is idling.")

                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                print("[*] Worker shutdown signal received.")
                break
            except Exception as e:
                print(f"[!] Worker loop exception: {str(e)}")
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)

        self.cleanup()

    def record_heartbeat(self):
        db = self.get_db()
        should_close = (self._db is None)
        try:
            hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == self.worker_id).first()
            if not hb:
                hb = WorkerHeartbeat(
                    worker_id=self.worker_id,
                    hostname=socket.gethostname(),
                    pid=os.getpid(),
                    status="healthy",
                    active_jobs_count=self.active_jobs
                )
                db.add(hb)
            else:
                hb.last_heartbeat = datetime.utcnow()
                hb.status = "busy" if self.active_jobs > 0 else "healthy"
                hb.active_jobs_count = self.active_jobs
            db.commit()
        finally:
            if should_close:
                db.close()

    def recover_unfinished_jobs(self, db: Optional[Session] = None):
        """
        On worker startup, safely recover jobs that were left in 'running' state
        due to an unexpected process restart. Re-verifies scope validity before retrying.
        """
        target_db = db or self.get_db()
        should_close = (db is None and self._db is None)
        try:
            stuck_jobs = target_db.query(ResearchJob).filter(ResearchJob.status == "running").all()
            for job in stuck_jobs:
                print(f"[*] Recovering interrupted job '{job.id}' ({job.title})...")
                # Check retry limit
                if job.retry_count >= job.max_retries:
                    job.status = "failed"
                    job.error_message = f"Job exceeded max retries ({job.max_retries}) following worker restarts."
                    continue

                # Check if scope is still active
                scope_active = True
                if job.scope_id:
                    scope = target_db.query(ScopeEntry).filter(ScopeEntry.id == job.scope_id).first()
                    if not scope or scope.status != "active":
                        scope_active = False

                if not scope_active:
                    job.status = "failed"
                    job.error_message = "Recovery aborted: Scope authorization has expired or changed during outage."
                else:
                    # Re-queue with exponential backoff increment
                    job.retry_count += 1
                    job.status = "queued"
                    job.error_message = f"Re-queued after worker recovery (attempt {job.retry_count}/{job.max_retries})."

            target_db.commit()
        finally:
            if should_close:
                target_db.close()

    async def process_next_job(self) -> bool:
        db: Session = SessionLocal()
        try:
            # Duplicate-job prevention: check if another worker is already running this target
            job = db.query(ResearchJob).filter(
                ResearchJob.status == "queued",
                ResearchJob.cancellation_requested == False
            ).order_by(ResearchJob.priority.asc(), ResearchJob.created_at.asc()).first()

            if not job:
                return False

            # Check if there is already another active job on this identical target to prevent duplicates
            duplicate_running = db.query(ResearchJob).filter(
                ResearchJob.target == job.target,
                ResearchJob.status == "running",
                ResearchJob.id != job.id
            ).first()

            if duplicate_running:
                print(f"[*] Postponing job {job.id}: another job is actively scanning target '{job.target}'.")
                return False

            self.active_jobs += 1
            print(f"[*] Processing Research Job: {job.title} [{job.id}] -> Target: {job.target}")

            # Record attempt
            attempt = JobAttempt(
                job_id=job.id,
                attempt_number=job.retry_count + 1,
                status="running"
            )
            db.add(attempt)
            db.commit()

            # Execute via MultiAgentOrchestrator
            orchestrator = MultiAgentOrchestrator(db)
            res = await orchestrator.execute_job(job.id)

            attempt.ended_at = datetime.utcnow()
            attempt.status = "completed" if res.get("success") else "failed"
            attempt.logs = str(res)
            db.commit()
            return True

        except Exception as e:
            print(f"[!] Error processing job: {str(e)}")
            return False
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)
            db.close()

    def cleanup(self):
        db: Session = SessionLocal()
        try:
            hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == self.worker_id).first()
            if hb:
                hb.status = "stopped"
                db.commit()
        finally:
            db.close()

if __name__ == "__main__":
    worker = AutonomousWorker()
    asyncio.run(worker.start())
