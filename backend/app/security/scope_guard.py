import fnmatch
import urllib.parse
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models import ScopeEntry, AuthorizedProgram
from app.config import settings

class ScopeValidationError(Exception):
    """Raised when a target fails authorization or scope validation."""
    pass

def normalize_target(target: str) -> str:
    """Normalizes target string for matching."""
    target = target.strip()
    if target.startswith("https://"):
        target = target[8:]
    elif target.startswith("http://"):
        target = target[7:]
    return target.rstrip("/").lower()

def is_domain_match(pattern: str, target_domain: str) -> bool:
    """
    Checks if a target domain matches a pattern.
    Handles exact domains ('example.com') and wildcard domains ('*.example.com').
    Never permits wildcard matching on arbitrary parent domains.
    """
    pattern = pattern.strip().lower()
    target_domain = target_domain.strip().lower()
    
    if pattern.startswith("*."):
        parent_domain = pattern[2:]
        # Must either match the parent domain or end with .parent_domain
        if target_domain == parent_domain:
            return True
        if target_domain.endswith("." + parent_domain):
            return True
        return False
    else:
        return pattern == target_domain

def validate_target_scope(
    db: Session,
    program_id: str,
    target: str,
    requested_method: str = "passive"
) -> Tuple[bool, str, Optional[ScopeEntry]]:
    """
    Validates whether a target is explicitly authorized in the Scope Registry for the given Program.
    Enforces FAIL-CLOSED logic:
    - If program doesn't exist or is inactive -> Denied.
    - If no active scope entry matches target -> Denied.
    - If requested method is prohibited or not in permitted methods -> Denied.
    - If Emergency Stop is active -> Denied.
    """
    if settings.EMERGENCY_STOP:
        return False, "Emergency Stop is active. All research operations are halted.", None
        
    if not target or not target.strip():
        return False, "Target cannot be empty.", None

    # Fetch authorized program
    program = db.query(AuthorizedProgram).filter(
        AuthorizedProgram.id == program_id,
        AuthorizedProgram.is_active == True
    ).first()
    
    if not program:
        return False, f"Authorized Program ID '{program_id}' not found or is currently inactive. Fail-closed.", None

    # Fetch active scope entries for this program
    active_scopes = db.query(ScopeEntry).filter(
        ScopeEntry.program_id == program_id,
        ScopeEntry.status == "active"
    ).all()
    
    if not active_scopes:
        return False, f"No active scope entries registered for program '{program.name}'. Research disallowed.", None

    # Parse target
    parsed_target = urllib.parse.urlparse(target if "://" in target else f"https://{target}")
    target_host = (parsed_target.hostname or target).lower()
    target_norm = normalize_target(target)

    matching_scope: Optional[ScopeEntry] = None

    for scope in active_scopes:
        scope_val = scope.target_value.strip().lower()
        
        if scope.target_type in ("domain", "wildcard_domain"):
            clean_scope_val = scope_val.replace("https://", "").replace("http://", "").split("/")[0]
            if is_domain_match(clean_scope_val, target_host):
                matching_scope = scope
                break
        elif scope.target_type == "url_prefix":
            scope_norm = normalize_target(scope_val)
            if target_norm.startswith(scope_norm):
                matching_scope = scope
                break
        elif scope.target_type in ("repository", "android_package", "cloud_config"):
            scope_norm = normalize_target(scope_val)
            if target_norm == scope_norm or fnmatch.fnmatch(target_norm, scope_norm):
                matching_scope = scope
                break

    if not matching_scope:
        return False, f"Target '{target}' is NOT in the authorized scope for program '{program.name}'. Access denied (Fail-Closed).", None

    # Validate methods
    permitted = [m.strip().lower() for m in (matching_scope.permitted_methods or "").split(",") if m.strip()]
    prohibited = [m.strip().lower() for m in (matching_scope.prohibited_methods or "").split(",") if m.strip()]
    req_method_norm = requested_method.strip().lower()

    if req_method_norm in prohibited:
        return False, f"Requested method '{requested_method}' is expressly PROHIBITED by scope authorization policy ({matching_scope.authorization_reference}).", None

    if permitted and "*" not in permitted and req_method_norm not in permitted:
        return False, f"Requested method '{requested_method}' is not in permitted methods list ({matching_scope.permitted_methods}).", None

    return True, f"Target '{target}' authorized under policy '{matching_scope.authorization_reference}'.", matching_scope
