from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuthorizedProgram, ScopeEntry, AuditEvent
from app.schemas import (
    AuthorizedProgramCreate, AuthorizedProgramResponse,
    ScopeEntryCreate, ScopeEntryUpdate, ScopeEntryResponse
)
from app.security.auth import get_current_active_user, require_roles
from app.security.scope_guard import validate_target_scope

router = APIRouter(tags=["Scope & Authorization"])

# --- Programs ---
@router.get("/api/programs", response_model=List[AuthorizedProgramResponse])
def list_programs(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    programs = db.query(AuthorizedProgram).all()
    res = []
    for p in programs:
        p_dict = {
            "id": p.id,
            "name": p.name,
            "organization": p.organization,
            "policy_url": p.policy_url,
            "contact_info": p.contact_info,
            "notes": p.notes,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "scopes_count": len(p.scopes)
        }
        res.append(p_dict)
    return res

@router.post("/api/programs", response_model=AuthorizedProgramResponse)
def create_program(
    prog_in: AuthorizedProgramCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    existing = db.query(AuthorizedProgram).filter(AuthorizedProgram.name == prog_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Program with this name already exists.")

    program = AuthorizedProgram(**prog_in.dict())
    db.add(program)
    db.commit()
    db.refresh(program)

    audit = AuditEvent(
        user_id=current_user.id,
        action="PROGRAM_CREATE",
        resource_type="program",
        resource_id=program.id,
        details=f"Created program '{program.name}' ({program.organization})."
    )
    db.add(audit)
    db.commit()

    return program

# --- Scopes ---
@router.get("/api/scopes", response_model=List[ScopeEntryResponse])
def list_scopes(
    program_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(ScopeEntry)
    if program_id:
        query = query.filter(ScopeEntry.program_id == program_id)
    if status_filter:
        query = query.filter(ScopeEntry.status == status_filter)
    return query.order_by(ScopeEntry.created_at.desc()).all()

@router.post("/api/scopes", response_model=ScopeEntryResponse)
def create_scope_entry(
    scope_in: ScopeEntryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    # Verify program exists and is active
    program = db.query(AuthorizedProgram).filter(
        AuthorizedProgram.id == scope_in.program_id,
        AuthorizedProgram.is_active == True
    ).first()
    if not program:
        raise HTTPException(status_code=400, detail="Program not found or inactive. Cannot bind scope.")

    scope = ScopeEntry(**scope_in.dict())
    db.add(scope)
    db.commit()
    db.refresh(scope)

    audit = AuditEvent(
        user_id=current_user.id,
        action="SCOPE_ENTRY_CREATE",
        resource_type="scope",
        resource_id=scope.id,
        details=f"Added scope '{scope.target_value}' to program '{program.name}' under policy '{scope.authorization_reference}'."
    )
    db.add(audit)
    db.commit()

    return scope

@router.put("/api/scopes/{scope_id}", response_model=ScopeEntryResponse)
def update_scope_entry(
    scope_id: str,
    scope_update: ScopeEntryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "researcher"]))
):
    scope = db.query(ScopeEntry).filter(ScopeEntry.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="Scope entry not found.")

    for field, val in scope_update.dict(exclude_unset=True).items():
        setattr(scope, field, val)

    db.commit()
    db.refresh(scope)

    audit = AuditEvent(
        user_id=current_user.id,
        action="SCOPE_ENTRY_UPDATE",
        resource_type="scope",
        resource_id=scope.id,
        details=f"Updated scope '{scope.target_value}'. Status: {scope.status}."
    )
    db.add(audit)
    db.commit()

    return scope

@router.delete("/api/scopes/{scope_id}")
def delete_scope_entry(
    scope_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    scope = db.query(ScopeEntry).filter(ScopeEntry.id == scope_id).first()
    if not scope:
        raise HTTPException(status_code=404, detail="Scope entry not found.")

    db.delete(scope)
    db.commit()

    audit = AuditEvent(
        user_id=current_user.id,
        action="SCOPE_ENTRY_DELETE",
        resource_type="scope",
        resource_id=scope_id,
        details=f"Deleted scope '{scope.target_value}'."
    )
    db.add(audit)
    db.commit()

    return {"message": "Scope entry deleted successfully."}

@router.get("/api/scopes/validate-target")
def prevalidate_target(
    program_id: str,
    target: str,
    method: str = "passive",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pre-flight check to verify if a target would be authorized under the scope registry."""
    is_valid, msg, scope = validate_target_scope(db, program_id, target, requested_method=method)
    return {
        "authorized": is_valid,
        "message": msg,
        "scope_id": scope.id if scope else None,
        "authorization_reference": scope.authorization_reference if scope else None
    }
