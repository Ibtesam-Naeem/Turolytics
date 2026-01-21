# ------------------------------ IMPORTS ------------------------------
import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
# Only load .env for local/dev. On Railway, env vars come from the platform.
if ENVIRONMENT != "production":
    load_dotenv()

# ------------------------------ CONFIGURATION CLASSES ------------------------------
@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    database: str = os.getenv("DB_NAME", "turolytics2_0")
    
    @property
    def database_url(self) -> str:
        """Get SQLAlchemy database URL.
        
        Supports Railway's DATABASE_URL environment variable (preferred)
        or falls back to individual DB_* variables for local development.
        """
        # Railway provides DATABASE_URL automatically when PostgreSQL service is added
        railway_db_url = os.getenv("DATABASE_URL")
        if railway_db_url:
            # Railway's DATABASE_URL uses postgres:// but SQLAlchemy needs postgresql://
            if railway_db_url.startswith("postgres://"):
                railway_db_url = railway_db_url.replace("postgres://", "postgresql://", 1)
            return railway_db_url
        
        # Fallback to individual environment variables for local development
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class EmailConfig:
    """Email configuration."""
    provider: str = os.getenv("EMAIL_PROVIDER", "sendgrid")
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    from_email: str = os.getenv("EMAIL_FROM", "noreply@turolytics.com")
    from_name: str = os.getenv("EMAIL_FROM_NAME", "Turolytics")
    use_lambda: bool = os.getenv("EMAIL_USE_LAMBDA", "false").lower() == "true"
    lambda_function_name: Optional[str] = os.getenv("EMAIL_LAMBDA_FUNCTION", None)

@dataclass
class WaitlistAdminConfig:
    """Waitlist admin configuration."""
    password: str = os.getenv("WAITLIST_ADMIN_PASSWORD", "")
    session_secret: str = os.getenv("WAITLIST_SESSION_SECRET", os.getenv("SECRET_KEY", "change-me-in-production"))

# ------------------------------ MAIN SETTINGS CLASS ------------------------------

class Settings:
    """Main application settings."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.email = EmailConfig()
        self.waitlist_admin = WaitlistAdminConfig()
        
        self._setup_logging()
        self._validate_production_config()
    
    def _setup_logging(self):
        """Configure application logging."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def _validate_production_config(self) -> None:
        """Fail fast on unsafe production defaults."""
        if ENVIRONMENT != "production":
            return
        
        # Prevent deploying with a known placeholder secret.
        if not self.waitlist_admin.session_secret or self.waitlist_admin.session_secret == "change-me-in-production":
            raise ValueError(
                "Missing WAITLIST_SESSION_SECRET (or SECRET_KEY). "
                "Set a strong secret in Railway environment variables."
            )

# ------------------------------ GLOBAL SETTINGS INSTANCE ------------------------------
settings = Settings()

# ------------------------------ END OF FILE ------------------------------