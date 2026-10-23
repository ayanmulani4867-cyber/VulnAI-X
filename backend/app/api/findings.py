from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Finding, Evidence, AuditEvent
from app.schemas import FindingResponse, FindingUpdate
from app.security.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/findings", tags=["Findings"])

@router.get("", response_model=List[FindingResponse])
def list_findings(
    severity: Optional[str] = None,
    confidence: Optional[str] = None,
    status_filter: Optional[str] = None,
    program_id: Optional[str] = None,
    job_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity)
    if confidence:
        query = query.filter(Finding.confidence == confidence)
    if status_filter:
        query = query.filter(Finding.status == status_filter)
    if program_id:
        query = query.filter(Finding.program_id == program_id)
    if job_id:
        query = query.filter(Finding.job_id == job_id)

    return query.order_by(Finding.created_at.desc()).all()

@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")
    return finding

@router.patch("/{finding_id}", response_model=FindingResponse)
def update_finding(
    finding_id: str,
    update_data: FindingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")

    old_status = finding.status
    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(finding, field, val)

    db.commit()
    db.refresh(finding)

    audit = AuditEvent(
        user_id=current_user.id,
        action="FINDING_UPDATE",
        resource_type="finding",
        resource_id=finding.id,
        details=f"Updated finding '{finding.title}'. Status: {old_status} -> {finding.status}."
    )
    db.add(audit)
    db.commit()

    return finding
