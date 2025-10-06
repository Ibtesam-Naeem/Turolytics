# ------------------------------ IMPORTS ------------------------------
import os
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# ------------------------------ CONFIGURATION CLASSES ------------------------------
@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    url: str = os.getenv("DATABASE_URL", "")
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    def __post_init__(self):
        """Validate database configuration."""
        if not self.url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Example: postgresql://user:password@localhost:5432/dbname"
            )

@dataclass
class ScrapingConfig:
    """Scraping configuration."""
    timeout: int = int(os.getenv("SCRAPING_TIMEOUT", "300")) 
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    headless: bool = os.getenv("SCRAPING_HEADLESS", "true").lower() == "true"
    user_agent: str = os.getenv("SCRAPING_USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    retry_attempts: int = int(os.getenv("SCRAPING_RETRY_ATTEMPTS", "3"))
    session_expiry_hours: int = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))

@dataclass
class CORSConfig:
    """CORS configuration."""
    origins: str = os.getenv("CORS_ORIGINS", "*")
    credentials: bool = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    
    def get_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.origins.split(",")]

@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

@dataclass
class APIConfig:
    """API configuration."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"

@dataclass
class S3Config:
    """AWS S3 configuration."""
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    region: str = os.getenv("AWS_REGION", "us-east-1")
    bucket_name: str = os.getenv("S3_BUCKET_NAME", "")
    max_file_size: int = int(os.getenv("S3_MAX_FILE_SIZE", "10485760"))  # 10MB default
    allowed_extensions: str = os.getenv("S3_ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png,doc,docx,xls,xlsx,txt")
    
    def get_allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]
    
    def __post_init__(self):
        """Validate S3 configuration."""
        # Commented out for testing - S3 not needed for scraping
        # if not self.access_key_id or not self.secret_access_key:
        #     raise ValueError(
        #         "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are required for S3 functionality."
        #     )
        # if not self.bucket_name:
        #     raise ValueError(
        #         "S3_BUCKET_NAME environment variable is required for S3 functionality."
        #     )

# ------------------------------ MAIN SETTINGS CLASS ------------------------------

class Settings:
    """Main application settings."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.cors = CORSConfig()
        self.security = SecurityConfig()
        self.api = APIConfig()
        self.s3 = S3Config()
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure application logging."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

# ------------------------------ GLOBAL SETTINGS INSTANCE ------------------------------
settings = Settings()

# ------------------------------ END OF FILE ------------------------------