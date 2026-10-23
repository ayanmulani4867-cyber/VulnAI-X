from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

def get_normalized_database_url(url: str) -> str:
    """
    Normalizes database URL for SQLAlchemy 2.x and driver compatibility:
    1. Converts legacy 'postgres://' scheme to 'postgresql://'.
    2. Ensures SSL mode is enforced for cloud PostgreSQL connections (like Neon).
    """
    if not url:
        return "sqlite:///./vulnai_x.db"

    clean_url = url.strip()

    # Handle postgres:// -> postgresql://
    if clean_url.startswith("postgres://"):
        clean_url = "postgresql://" + clean_url[len("postgres://"):]

    # For PostgreSQL connections, ensure sslmode=require if connecting to remote host
    if clean_url.startswith("postgresql"):
        parsed = urlparse(clean_url)
        hostname = parsed.hostname or ""
        if hostname not in ("localhost", "127.0.0.1", ""):
            query_params = parse_qs(parsed.query)
            if "sslmode" not in query_params:
                query_params["sslmode"] = ["require"]
                new_query = urlencode(query_params, doseq=True)
                clean_url = urlunparse(parsed._replace(query=new_query))

    return clean_url

db_url = get_normalized_database_url(settings.DATABASE_URL)

# Configure connection pooling and connect_args depending on engine
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
else:
    # Optimized for Neon serverless PostgreSQL with connection pooler:
    # - pool_pre_ping: validates connections before checkout, recovering seamlessly from serverless auto-suspend
    # - pool_recycle: recycles idle connections every 5 mins to prevent stale sockets
    # - pool_size & max_overflow: provides sensible concurrency limits for FastAPI + autonomous worker
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connectivity() -> dict:
    """Safely verifies database connectivity and returns metadata."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            dialect = engine.dialect.name
            version = None
            if dialect == "postgresql":
                ver = conn.execute(text("SELECT version();")).scalar()
                version = ver.split(",")[0] if ver else None
            return {
                "connected": True,
                "dialect": dialect,
                "version": version,
                "error": None
            }
    except Exception as e:
        return {
            "connected": False,
            "dialect": engine.dialect.name if hasattr(engine, "dialect") else "unknown",
            "version": None,
            "error": str(e)
        }
