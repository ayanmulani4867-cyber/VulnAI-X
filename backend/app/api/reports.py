import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ResearchJob, Finding, AuthorizedProgram
from app.reporting.report_generator import ReportGenerator
from app.security.auth import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/job/{job_id}/json")
def export_job_report_json(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    program = db.query(AuthorizedProgram).filter(AuthorizedProgram.id == job.program_id).first()
    findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    report_json = ReportGenerator.generate_json_report(job, findings, program)
    return JSONResponse(content=report_json)

@router.get("/job/{job_id}/pdf")
def export_job_report_pdf(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    program = db.query(AuthorizedProgram).filter(AuthorizedProgram.id == job.program_id).first()
    findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    pdf_filename = f"vulnai_report_job_{job.id[:8]}.pdf"
    pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)

    ReportGenerator.generate_pdf_report(job, findings, program, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename
    )
