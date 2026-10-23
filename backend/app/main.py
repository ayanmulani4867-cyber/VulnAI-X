from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, AuthorizedProgram, ScopeEntry
from app.security.auth import get_password_hash
from app.api import auth, dashboard, scopes, jobs, findings, reports, settings as settings_api, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Schema
    Base.metadata.create_all(bind=engine)
    
    # Safe migration for existing SQLite and PostgreSQL DBs
    with engine.connect() as conn:
        try:
            if engine.dialect.name == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass

    # Auto-seed initial default admin and authorized programs if DB is fresh
    db = SessionLocal()
    try:
        # 1. Admin user setup check
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 0:
            initial_pass = settings.ADMIN_INITIAL_PASSWORD or "admin"
            admin = User(
                username="admin",
                email="admin@vulnaix.org",
                hashed_password=get_password_hash(initial_pass),
                role="admin",
                must_change_password=False
            )
            db.add(admin)
            print(f"[*] Default administrator 'admin' initialized with password '{initial_pass}'.")

        # 2. Google Vulnerability Reward Program
        google_vrp = db.query(AuthorizedProgram).filter(AuthorizedProgram.name == "Google VRP").first()
        if not google_vrp:
            google_vrp = AuthorizedProgram(
                name="Google VRP",
                organization="Google LLC",
                policy_url="https://bughunters.google.com/about/rules",
                contact_info="security@google.com",
                notes="Google Vulnerability Reward Program. Only explicitly listed assets are permitted."
            )
            db.add(google_vrp)
            db.flush()

            # Seed specific authorized domains
            s1 = ScopeEntry(
                program_id=google_vrp.id,
                target_type="wildcard_domain",
                target_value="*.google.com",
                permitted_methods="passive,headers,tls,code_review",
                prohibited_methods="dos,brute_force,credential_stuffing,data_exfiltration,social_engineering",
                rate_limit_rps=2.0,
                authorization_reference="Google Bughunters Policy 2026 v4.1 - In-Scope Web Applications",
                status="active"
            )
            s2 = ScopeEntry(
                program_id=google_vrp.id,
                target_type="domain",
                target_value="bughunters.google.com",
                permitted_methods="passive,headers,tls",
                prohibited_methods="dos,brute_force,credential_stuffing",
                rate_limit_rps=1.0,
                authorization_reference="Google Bughunters Scope Appendix A",
                status="active"
            )
            db.add_all([s1, s2])
            print("[+] Seeded Google VRP program & active scopes.")

        # 3. Meta Bug Bounty Program
        meta_bbp = db.query(AuthorizedProgram).filter(AuthorizedProgram.name == "Meta Bug Bounty").first()
        if not meta_bbp:
            meta_bbp = AuthorizedProgram(
                name="Meta Bug Bounty",
                organization="Meta Platforms Inc.",
                policy_url="https://www.facebook.com/whitehat",
                contact_info="whitehat@fb.com",
                notes="Meta Whitehat Program. Strict non-destructive testing requirements."
            )
            db.add(meta_bbp)
            db.flush()

            m1 = ScopeEntry(
                program_id=meta_bbp.id,
                target_type="wildcard_domain",
                target_value="*.meta.com",
                permitted_methods="passive,headers,tls,code_review",
                prohibited_methods="dos,brute_force,account_takeover,data_scraping",
                rate_limit_rps=1.5,
                authorization_reference="Meta Whitehat Terms 2026 - Section 2 (Authorized Testing)",
                status="active"
            )
            db.add(m1)
            print("[+] Seeded Meta Bug Bounty program & active scopes.")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding initial data: {str(e)}")
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VulnAI X — Autonomous AI Security Research Platform with Fail-Closed Scope Enforcement",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(scopes.router)
app.include_router(jobs.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(settings_api.router)
app.include_router(health.router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs"
    }
