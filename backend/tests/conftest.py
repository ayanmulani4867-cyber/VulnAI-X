import pytest
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import User, AuthorizedProgram, ScopeEntry
from app.security.auth import get_password_hash, create_access_token
from app.config import settings

# In-memory test SQLite DB
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_admin_user(db):
    user = User(
        username="admin_test",
        email="admintest@vulnaix.org",
        hashed_password=get_password_hash("StrongAdminPassword123!"),
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_token(test_admin_user):
    return create_access_token(data={"sub": test_admin_user.username, "role": test_admin_user.role})

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def sample_program_and_scope(db):
    program = AuthorizedProgram(
        name="Test Google VRP",
        organization="Google",
        policy_url="https://bughunters.google.com/rules",
        is_active=True
    )
    db.add(program)
    db.flush()

    scope = ScopeEntry(
        program_id=program.id,
        target_type="wildcard_domain",
        target_value="*.google.com",
        permitted_methods="passive,headers,tls",
        prohibited_methods="dos,brute_force",
        authorization_reference="VRP Policy Sec 2",
        status="active"
    )
    db.add(scope)
    db.commit()
    db.refresh(program)
    db.refresh(scope)
    return program, scope
