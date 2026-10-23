from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    APP_NAME: str = "VulnAI X"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="development, production, or testing")
    DEBUG: bool = False
    
    # Security & Auth
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="JWT Secret key. MUST be overridden in production."
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ADMIN_INITIAL_PASSWORD: Optional[str] = None
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./vulnai_x.db",
        description="SQLite for local, PostgreSQL for cloud"
    )
    
    # Emergency Stop - stops all active and scheduled jobs immediately
    EMERGENCY_STOP: bool = False
    
    # SSRF & Scope Safety
    ALLOW_PRIVATE_LAB_TARGETS: bool = Field(
        default=False,
        description="Only set to True in isolated mock testing labs. Blocks 127.0.0.1, 10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12, 169.254.169.254 by default."
    )
    MAX_REDIRECT_HOPS: int = 5
    REQUEST_TIMEOUT_SECONDS: int = 15
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Worker & Execution Limits
    MAX_CONCURRENT_JOBS: int = 3
    JOB_TIMEOUT_SECONDS: int = 900
    MAX_RETRY_ATTEMPTS: int = 3
    WORKER_POLL_INTERVAL_SECONDS: int = 5
    WORKER_HEARTBEAT_INTERVAL_SECONDS: int = 10
    
    # SMTP / Notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TLS: bool = True
    NOTIFICATION_EMAIL_TO: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Data directory
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    REPORTS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reports")
    UPLOADS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
