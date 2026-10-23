from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AuditEvent
from app.schemas import (
    UserCreate, UserResponse, Token, LoginRequest,
    InitialSetupRequest, ChangePasswordRequest, SetupStatusResponse
)
from app.security.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, validate_password_complexity
)
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/setup-status", response_model=SetupStatusResponse)
def get_setup_status(db: Session = Depends(get_db)):
    """Checks whether an administrator exists or if initial setup is required."""
    admin_exists = db.query(User).filter(User.role == "admin", User.is_active == True).first() is not None
    return SetupStatusResponse(setup_required=not admin_exists)

@router.post("/setup", response_model=Token)
def perform_initial_setup(setup_in: InitialSetupRequest, db: Session = Depends(get_db)):
    """Creates the initial administrator account. Permanently disabled once an admin exists."""
    admin_exists = db.query(User).filter(User.role == "admin", User.is_active == True).first() is not None
    if admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial setup is already completed. Please log in with your administrator account."
        )

    # Validate password complexity
    valid, msg = validate_password_complexity(setup_in.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = User(
        username=setup_in.username,
        email=setup_in.email,
        hashed_password=get_password_hash(setup_in.password),
        role="admin",
        must_change_password=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditEvent(
        user_id=user.id,
        action="INITIAL_SETUP_COMPLETED",
        resource_type="system",
        resource_id=user.id,
        details=f"Initial administrator '{user.username}' successfully configured."
    )
    db.add(audit)
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "must_change_password": False
    }

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enforces mandatory or requested password changes with full complexity validation."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    if req.current_password == req.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be identical to the current password."
        )

    valid, msg = validate_password_complexity(req.new_password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    current_user.hashed_password = get_password_hash(req.new_password)
    current_user.must_change_password = False
    db.commit()

    audit = AuditEvent(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        resource_type="user",
        resource_id=current_user.id,
        details=f"User '{current_user.username}' changed their password."
    )
    db.add(audit)
    db.commit()

    return {"message": "Password changed successfully. You may now access the platform."}

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered."
        )

    valid, msg = validate_password_complexity(user_in.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # First user registered is an admin, others researcher
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else user_in.role

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        must_change_password=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditEvent(
        user_id=user.id,
        action="USER_REGISTER",
        resource_type="user",
        resource_id=user.id,
        details=f"User {user.username} registered with role {user.role}."
    )
    db.add(audit)
    db.commit()

    return user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "must_change_password": user.must_change_password
    }

@router.post("/login", response_model=Token)
def login_json(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "must_change_password": user.must_change_password
    }

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
