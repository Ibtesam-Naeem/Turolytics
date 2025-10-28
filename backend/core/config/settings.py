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

# ------------------------------ MAIN SETTINGS CLASS ------------------------------

class Settings:
    """Main application settings."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.cors = CORSConfig()
        self.security = SecurityConfig()
        self.api = APIConfig()
        
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