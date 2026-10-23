import pytest
from app.security.scope_guard import validate_target_scope
from app.models import ScopeEntry

def test_target_in_scope_authorized(db, sample_program_and_scope):
    program, scope = sample_program_and_scope
    is_valid, msg, matched_scope = validate_target_scope(
        db, program.id, "https://subdomain.google.com/login", requested_method="passive"
    )
    assert is_valid is True
    assert matched_scope.id == scope.id
    assert "authorized under policy" in msg.lower()

def test_out_of_scope_target_rejected(db, sample_program_and_scope):
    program, _ = sample_program_and_scope
    # Target that does NOT match *.google.com
    is_valid, msg, matched_scope = validate_target_scope(
        db, program.id, "https://unauthorized-domain.com", requested_method="passive"
    )
    assert is_valid is False
    assert matched_scope is None
    assert "not in the authorized scope" in msg.lower()

def test_prohibited_method_rejected(db, sample_program_and_scope):
    program, _ = sample_program_and_scope
    is_valid, msg, _ = validate_target_scope(
        db, program.id, "https://subdomain.google.com", requested_method="dos"
    )
    assert is_valid is False
    assert "prohibited" in msg.lower()

def test_paused_scope_rejected(db, sample_program_and_scope):
    program, scope = sample_program_and_scope
    scope.status = "paused"
    db.commit()

    is_valid, msg, _ = validate_target_scope(
        db, program.id, "https://subdomain.google.com", requested_method="passive"
    )
    assert is_valid is False
    assert "no active scope entries" in msg.lower()

def test_prevalidate_endpoint(client, auth_headers, sample_program_and_scope):
    program, _ = sample_program_and_scope
    # Authorized target
    resp = client.get(
        f"/api/scopes/validate-target?program_id={program.id}&target=https://mail.google.com&method=passive",
        headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["authorized"] is True

    # Out of scope target
    resp2 = client.get(
        f"/api/scopes/validate-target?program_id={program.id}&target=https://evil.corp&method=passive",
        headers=auth_headers
    )
    assert resp2.status_code == 200
    assert resp2.json()["authorized"] is False
