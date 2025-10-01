# ------------------------------ IMPORTS ------------------------------
import os
import logging
from typing import List, Optional
from dataclasses import dataclass

# ------------------------------ CONFIGURATION CLASSES ------------------------------
@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = os.getenv("DATABASE_URL", "")
    use_sqlite: bool = os.getenv("USE_SQLITE", "false").lower() == "true"
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    def __post_init__(self):
        """Validate database configuration."""
        if not self.url and not self.use_sqlite:
            self.use_sqlite = True

@dataclass
class ScrapingConfig:
    """Scraping configuration."""
    timeout: int = int(os.getenv("SCRAPING_TIMEOUT", "300"))  # 5 minutes
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    headless: bool = os.getenv("SCRAPING_HEADLESS", "true").lower() == "true"
    user_agent: str = os.getenv("SCRAPING_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    retry_attempts: int = int(os.getenv("SCRAPING_RETRY_ATTEMPTS", "3"))
    session_expiry_hours: int = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))  # 24 hours default

@dataclass
class BouncieConfig:
    """Bouncie API configuration (future integration)."""
    api_key: str = os.getenv("BOUNCIE_API_KEY", "")
    base_url: str = os.getenv("BOUNCIE_BASE_URL", "https://api.bouncie.com")
    timeout: int = int(os.getenv("BOUNCIE_TIMEOUT", "30"))

@dataclass
class PlaidConfig:
    """Plaid API configuration (future integration)."""
    client_id: str = os.getenv("PLAID_CLIENT_ID", "")
    secret: str = os.getenv("PLAID_SECRET", "")
    environment: str = os.getenv("PLAID_ENVIRONMENT", "sandbox")
    base_url: str = os.getenv("PLAID_BASE_URL", "https://sandbox.plaid.com")

@dataclass
class AmazonS3Config:
    """Amazon S3 configuration (future integration)."""
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    bucket_name: str = os.getenv("AWS_S3_BUCKET", "")
    region: str = os.getenv("AWS_REGION", "us-east-1")

class Settings:
    """Main application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Turolytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_CREDENTIALS: bool = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    def __init__(self):
        """Initialize settings and validate configuration."""
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        
        self.bouncie = BouncieConfig()
        self.plaid = PlaidConfig()
        self.amazon_s3 = AmazonS3Config()
        
        self._validate_config()
    
    def _validate_config(self):
        """Validate main configuration settings."""
        logger = logging.getLogger(__name__)
        
        if self.DEBUG and self.CORS_ORIGINS == ["*"]:
            logger.warning("CORS is set to allow all origins in DEBUG mode")
        
        if self.SECRET_KEY == "your-secret-key-here" and not self.DEBUG:
            logger.warning("Using default secret key in production")
    
    # ------------------------------ CONVENIENCE METHODS ------------------------------
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL."""
        if self.database.use_sqlite:
            return "sqlite:///./turolytics.db"
        return self.database.url
    
    def get_enabled_integrations(self) -> List[str]:
        """Get list of enabled integrations."""
        enabled = []
        if self.bouncie.api_key:
            enabled.append("bouncie")
        if self.plaid.client_id and self.plaid.secret:
            enabled.append("plaid")
        if self.amazon_s3.access_key_id and self.amazon_s3.secret_access_key:
            enabled.append("amazon_s3")
        return enabled
    
    def get_integration_config(self, name: str) -> Optional[object]:
        """Fetch integration-specific config (future-proof)."""
        integrations = {
            "bouncie": self.bouncie,
            "plaid": self.plaid,
            "amazon_s3": self.amazon_s3,
        }
        return integrations.get(name)
    
    def is_integration_enabled(self, name: str) -> bool:
        """Check if a specific integration is enabled."""
        return name in self.get_enabled_integrations()

# ------------------------------ INSTANCE ------------------------------
settings = Settings()