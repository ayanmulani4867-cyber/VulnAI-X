import pytest
from app.models import User
from app.security.auth import get_password_hash, create_access_token

def test_user_registration(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "researcher1", "email": "r1@example.com", "password": "SecurePassword123!", "role": "researcher"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "researcher1"
    assert "password" not in data

def test_duplicate_user_rejected(client):
    client.post(
        "/api/auth/register",
        json={"username": "dup_user", "email": "dup@example.com", "password": "Password123!@#"}
    )
    response = client.post(
        "/api/auth/register",
        json={"username": "dup_user", "email": "dup2@example.com", "password": "Password123!@#"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_weak_password_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "weak_user", "email": "weak@example.com", "password": "weak"}
    )
    assert response.status_code == 400
    assert "at least 12 characters" in response.json()["detail"]

def test_login_flow(client):
    client.post(
        "/api/auth/register",
        json={"username": "login_user", "email": "login@example.com", "password": "MySecretPassword123!"}
    )
    # Login via /api/auth/login JSON
    response = client.post(
        "/api/auth/login",
        json={"username": "login_user", "password": "MySecretPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["must_change_password"] is False

    # Access /api/auth/me
    token = data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "login_user"

def test_unauthenticated_request_fails(client):
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 401

def test_initial_setup_flow(client, db):
    # Remove all admin users from test session
    db.query(User).filter(User.role == "admin").delete()
    db.commit()

    # Check setup status
    status_resp = client.get("/api/auth/setup-status")
    assert status_resp.status_code == 200
    assert status_resp.json()["setup_required"] is True

    # Complete initial setup
    setup_resp = client.post(
        "/api/auth/setup",
        json={"username": "lead_admin", "email": "lead@vulnaix.org", "password": "InitialAdminPass2026!@#"}
    )
    assert setup_resp.status_code == 200
    assert "access_token" in setup_resp.json()
    assert setup_resp.json()["must_change_password"] is False

    # Subsequent setup attempt must fail
    dup_setup = client.post(
        "/api/auth/setup",
        json={"username": "hacker_admin", "email": "hacker@evil.corp", "password": "AttackerPass123!@#"}
    )
    assert dup_setup.status_code == 400
    assert "already completed" in dup_setup.json()["detail"]

def test_password_change_flow(client, db):
    user = User(
        username="temp_user",
        email="temp@example.com",
        hashed_password=get_password_hash("OldPassword123!@#"),
        role="researcher",
        must_change_password=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.username, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    # Protected endpoint should reject access when must_change_password is True
    blocked_resp = client.get("/api/dashboard/stats", headers=headers)
    assert blocked_resp.status_code == 403
    assert "Password change required" in blocked_resp.json()["detail"]

    # Attempt to change with wrong current password
    fail_resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "WrongPassword123!", "new_password": "NewSecurePassword2026!@#"},
        headers=headers
    )
    assert fail_resp.status_code == 400

    # Successful password change
    succ_resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "OldPassword123!@#", "new_password": "NewSecurePassword2026!@#"},
        headers=headers
    )
    assert succ_resp.status_code == 200

    # User must now be able to access protected endpoints
    allowed_resp = client.get("/api/dashboard/stats", headers=headers)
    assert allowed_resp.status_code == 200
