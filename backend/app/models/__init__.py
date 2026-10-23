from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="researcher")  # admin, researcher, viewer
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class AuthorizedProgram(Base):
    __tablename__ = "authorized_programs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True) # e.g. "Google VRP", "Meta Bug Bounty"
    organization = Column(String(100), nullable=False)
    policy_url = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scopes = relationship("ScopeEntry", back_populates="program", cascade="all, delete-orphan")
    jobs = relationship("ResearchJob", back_populates="program")
    findings = relationship("Finding", back_populates="program")

class ScopeEntry(Base):
    __tablename__ = "scope_entries"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    program_id = Column(String(36), ForeignKey("authorized_programs.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(30), nullable=False) # domain, wildcard_domain, url_prefix, repository, android_package, cloud_config
    target_value = Column(String(255), nullable=False, index=True) # e.g. "*.google.com", "https://auth.meta.com", "github.com/org/repo"
    permitted_methods = Column(Text, default="passive,headers,tls,code_review") # comma-separated or text
    prohibited_methods = Column(Text, default="dos,brute_force,credential_stuffing,data_exfiltration,social_engineering")
    rate_limit_rps = Column(Float, default=1.0)
    authorization_reference = Column(String(255), nullable=False) # e.g. "VRP Program Policy 2026.1, Section 3.2"
    date_last_reviewed = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active") # active, paused, expired, revoked
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    program = relationship("AuthorizedProgram", back_populates="scopes")
    jobs = relationship("ResearchJob", back_populates="scope")

class ResearchJob(Base):
    __tablename__ = "research_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    program_id = Column(String(36), ForeignKey("authorized_programs.id"), nullable=False)
    scope_id = Column(String(36), ForeignKey("scope_entries.id"), nullable=True)
    title = Column(String(200), nullable=False)
    target = Column(String(500), nullable=False)
    module_type = Column(String(30), nullable=False) # web, api, code, mobile, cloud, ai_sec, full_suite
    status = Column(String(20), default="queued", index=True) # queued, running, completed, failed, cancelled, timeout
    priority = Column(Integer, default=5) # 1 highest, 10 lowest
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    cancellation_requested = Column(Boolean, default=False)
    is_scheduled = Column(Boolean, default=False)
    cron_expression = Column(String(50), nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(50), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    program = relationship("AuthorizedProgram", back_populates="jobs")
    scope = relationship("ScopeEntry", back_populates="jobs")
    findings = relationship("Finding", back_populates="job", cascade="all, delete-orphan")
    attempts = relationship("JobAttempt", back_populates="job", cascade="all, delete-orphan")
    tool_results = relationship("ToolResult", back_populates="job", cascade="all, delete-orphan")

class JobAttempt(Base):
    __tablename__ = "job_attempts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    logs = Column(Text, default="")
    
    job = relationship("ResearchJob", back_populates="attempts")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True)
    program_id = Column(String(36), ForeignKey("authorized_programs.id"), nullable=False)
    scope_id = Column(String(36), ForeignKey("scope_entries.id"), nullable=True)
    
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False) # e.g. "Headers", "CORS", "Authentication", "Dependency", "Hardcoded Secret", "IaC Misconfig"
    severity = Column(String(20), nullable=False, index=True) # Critical, High, Medium, Low, Informational
    confidence = Column(String(20), nullable=False, index=True) # Certain, High, Medium, Low
    status = Column(String(40), default="Detected", index=True)
    # Statuses: Detected, Needs Investigation, Verification Pending, Verified in Authorized Environment, False Positive, Fixed, Retest Required
    
    target = Column(String(500), nullable=False)
    evidence_summary = Column(Text, nullable=False)
    reproduction_steps = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    tool_name = Column(String(100), nullable=True)
    rule_id = Column(String(150), nullable=True)
    false_positive_reason = Column(Text, nullable=True)
    duplicate_of_id = Column(String(36), ForeignKey("findings.id"), nullable=True)
    
    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_observed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = relationship("ResearchJob", back_populates="findings")
    program = relationship("AuthorizedProgram", back_populates="findings")
    evidence_items = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")
    duplicates = relationship("Finding", remote_side=[id])

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(String(50), nullable=False) # http_request, http_response, code_snippet, ast_trace, log_output, config_dump
    content = Column(Text, nullable=False)
    headers_json = Column(Text, nullable=True)
    request_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    finding = relationship("Finding", back_populates="evidence_items")

class ToolResult(Base):
    __tablename__ = "tool_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    raw_output = Column(Text, nullable=True)
    structured_json = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0)
    exit_code = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("ResearchJob", back_populates="tool_results")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False) # e.g. "AUTH_LOGIN", "SCOPE_CREATE", "JOB_START", "EMERGENCY_STOP"
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    recipient = Column(String(120), nullable=False)
    subject = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False) # finding_high_confidence, finding_verified, job_failed, worker_unhealthy
    status = Column(String(20), default="sent") # sent, failed, suppressed
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    worker_id = Column(String(100), unique=True, nullable=False)
    hostname = Column(String(100), nullable=True)
    pid = Column(Integer, nullable=True)
    status = Column(String(20), default="healthy") # healthy, busy, stopped, degraded
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    active_jobs_count = Column(Integer, default=0)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
