from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

# --- Auth & User ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "researcher"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    must_change_password: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    must_change_password: bool = False

class LoginRequest(BaseModel):
    username: str
    password: str

class InitialSetupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SetupStatusResponse(BaseModel):
    setup_required: bool

# --- Programs & Scope ---
class AuthorizedProgramBase(BaseModel):
    name: str
    organization: str
    policy_url: Optional[str] = None
    contact_info: Optional[str] = None
    notes: Optional[str] = None

class AuthorizedProgramCreate(AuthorizedProgramBase):
    pass

class AuthorizedProgramResponse(AuthorizedProgramBase):
    id: str
    is_active: bool
    created_at: datetime
    scopes_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ScopeEntryBase(BaseModel):
    program_id: str
    target_type: str # domain, wildcard_domain, url_prefix, repository, android_package, cloud_config
    target_value: str
    permitted_methods: str = "passive,headers,tls,code_review"
    prohibited_methods: str = "dos,brute_force,credential_stuffing,data_exfiltration,social_engineering"
    rate_limit_rps: float = 1.0
    authorization_reference: str
    status: str = "active"
    notes: Optional[str] = None

class ScopeEntryCreate(ScopeEntryBase):
    pass

class ScopeEntryUpdate(BaseModel):
    target_type: Optional[str] = None
    target_value: Optional[str] = None
    permitted_methods: Optional[str] = None
    prohibited_methods: Optional[str] = None
    rate_limit_rps: Optional[float] = None
    authorization_reference: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ScopeEntryResponse(ScopeEntryBase):
    id: str
    date_last_reviewed: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Research Jobs ---
class ResearchJobCreate(BaseModel):
    program_id: str
    target: str
    module_type: str = "web" # web, api, code, mobile, cloud, ai_sec, full_suite
    title: Optional[str] = None
    is_scheduled: bool = False
    cron_expression: Optional[str] = None

class JobAttemptResponse(BaseModel):
    id: str
    attempt_number: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    logs: str

    model_config = ConfigDict(from_attributes=True)

class ResearchJobResponse(BaseModel):
    id: str
    program_id: str
    scope_id: Optional[str] = None
    title: str
    target: str
    module_type: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    cancellation_requested: bool
    is_scheduled: bool
    cron_expression: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    findings_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# --- Findings & Evidence ---
class EvidenceCreate(BaseModel):
    evidence_type: str
    content: str
    headers_json: Optional[str] = None
    request_url: Optional[str] = None

class EvidenceResponse(EvidenceCreate):
    id: str
    finding_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FindingCreate(BaseModel):
    job_id: Optional[str] = None
    program_id: str
    scope_id: Optional[str] = None
    title: str
    category: str
    severity: str # Critical, High, Medium, Low, Informational
    confidence: str # Certain, High, Medium, Low
    status: str = "Detected"
    target: str
    evidence_summary: str
    reproduction_steps: Optional[str] = None
    impact: Optional[str] = None
    remediation: Optional[str] = None
    tool_name: Optional[str] = None
    rule_id: Optional[str] = None

class FindingUpdate(BaseModel):
    status: Optional[str] = None
    confidence: Optional[str] = None
    severity: Optional[str] = None
    remediation: Optional[str] = None
    false_positive_reason: Optional[str] = None

class FindingResponse(BaseModel):
    id: str
    job_id: Optional[str] = None
    program_id: str
    scope_id: Optional[str] = None
    title: str
    category: str
    severity: str
    confidence: str
    status: str
    target: str
    evidence_summary: str
    reproduction_steps: Optional[str] = None
    impact: Optional[str] = None
    remediation: Optional[str] = None
    tool_name: Optional[str] = None
    rule_id: Optional[str] = None
    false_positive_reason: Optional[str] = None
    first_detected_at: datetime
    last_observed_at: datetime
    created_at: datetime
    evidence_items: List[EvidenceResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Dashboard & System ---
class DashboardStats(BaseModel):
    total_jobs: int
    running_jobs: int
    potential_vulnerabilities: int
    verified_findings: int
    false_positives: int
    critical_and_high: int
    worker_health: str
    last_scheduled_run: Optional[datetime] = None
    active_scopes_count: int
    recent_activity: List[Dict[str, Any]] = []

class EmergencyStopRequest(BaseModel):
    reason: str = "Manual Emergency Stop initiated by researcher"

class EmailTestRequest(BaseModel):
    recipient: EmailStr

class SystemHealthResponse(BaseModel):
    status: str
    database: str
    worker_status: str
    last_heartbeat: Optional[datetime] = None
    active_jobs: int
    emergency_stop: bool
    version: str
