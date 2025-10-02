# ------------------------------ IMPORTS ------------------------------
import asyncio
import aiohttp
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from core.utils.logger import logger
from core.config.settings import settings

load_dotenv()

# ------------------------------ CONFIGURATION ------------------------------

@dataclass
class BouncieConfig:
    """Bouncie OAuth 2.0 configuration."""
    client_id: str = os.getenv("BOUNCIE_CLIENT_ID", "turolytics-dev")
    client_secret: str = os.getenv("BOUNCIE_CLIENT_SECRET", "")
    redirect_uri: str = os.getenv("BOUNCIE_REDIRECT_URI", "http://localhost:8000/auth/bouncie/callback")
    auth_url: str = "https://auth.bouncie.com/dialog/authorize"
    token_url: str = "https://auth.bouncie.com/oauth/token"
    api_base_url: str = "https://api.bouncie.dev/v1"
    scope: str = "vehicles trips locations user"
    token_refresh_buffer_minutes: int = int(os.getenv("BOUNCIE_TOKEN_REFRESH_BUFFER", "5"))
    auto_refresh_interval_seconds: int = int(os.getenv("BOUNCIE_AUTO_REFRESH_INTERVAL", "300"))
    
    def __post_init__(self):
        """Validate Bouncie configuration."""
        if not self.client_secret:
            raise ValueError(
                "BOUNCIE_CLIENT_SECRET environment variable is required. "
                "Get it from your Bouncie Developer Portal application."
            )

# ------------------------------ DATA CLASSES ------------------------------

@dataclass
class BouncieToken:
    """Bouncie access token with metadata."""
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=1)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until expiration."""
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (within buffer time)."""
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (self.expires_at - buffer)

# ------------------------------ AUTHENTICATION MANAGER ------------------------------

class BouncieAuthManager:
    """Manages Bouncie OAuth 2.0 authentication and token refresh."""
    
    def __init__(self):
        self.config = BouncieConfig()
        self.current_token: Optional[BouncieToken] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._is_refreshing = False
        logger.info("BouncieAuthManager initialized")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth 2.0 authorization URL."""
        try:
            params = {
                "response_type": "code",
                "client_id": self.config.client_id,
                "redirect_uri": self.config.redirect_uri,
                "scope": self.config.scope
            }
            if state:
                params["state"] = state
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            auth_url = f"{self.config.auth_url}?{query_string}"
            
            logger.info(f"Generated authorization URL for client {self.config.client_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise
    
    async def exchange_code_for_token(self, authorization_code: str) -> BouncieToken:
        """Exchange authorization code for access token."""
        try:
            logger.info("Exchanging authorization code for access token...")
            
            async with aiohttp.ClientSession() as session:
                data = {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.config.redirect_uri
                }
                
                async with session.post(
                    self.config.token_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        
                        # Parse JWT token to get expiration
                        access_token = token_data.get("access_token")
                        expires_at = self._parse_token_expiration(access_token)
                        
                        token = BouncieToken(
                            access_token=access_token,
                            token_type=token_data.get("token_type", "Bearer"),
                            expires_at=expires_at,
                            refresh_token=token_data.get("refresh_token"),
                            scope=token_data.get("scope"),
                            user_id=self._extract_user_id_from_token(access_token)
                        )
                        
                        self.current_token = token
                        logger.info(f"Successfully obtained Bouncie token, expires at {expires_at}")
                        return token
                    else:
                        error_text = await response.text()
                        logger.error(f"Token exchange failed: HTTP {response.status} - {error_text}")
                        raise Exception(f"Token exchange failed: HTTP {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    async def refresh_token(self) -> BouncieToken:
        """Refresh the access token using refresh token."""
        if not self.current_token or not self.current_token.refresh_token:
            logger.warning("No refresh token available")
            raise Exception("No refresh token available")
        
        if self._is_refreshing:
            logger.info("Token refresh already in progress, waiting...")
            while self._is_refreshing:
                await asyncio.sleep(0.1)
            return self.current_token
        
        self._is_refreshing = True
        
        try:
            logger.info("Refreshing Bouncie access token...")
            
            async with aiohttp.ClientSession() as session:
                data = {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.current_token.refresh_token
                }
                
                async with session.post(
                    self.config.token_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        
                        # Parse new token
                        access_token = token_data.get("access_token")
                        expires_at = self._parse_token_expiration(access_token)
                        
                        # Update current token
                        self.current_token = BouncieToken(
                            access_token=access_token,
                            token_type=token_data.get("token_type", "Bearer"),
                            expires_at=expires_at,
                            refresh_token=token_data.get("refresh_token", self.current_token.refresh_token),
                            scope=token_data.get("scope", self.current_token.scope),
                            user_id=self.current_token.user_id,
                            created_at=self.current_token.created_at
                        )
                        
                        logger.info(f"Successfully refreshed Bouncie token, expires at {expires_at}")
                        return self.current_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: HTTP {response.status} - {error_text}")
                        raise Exception(f"Token refresh failed: HTTP {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
        finally:
            self._is_refreshing = False
    
    def _parse_token_expiration(self, access_token: str) -> datetime:
        """Parse JWT token to extract expiration time."""
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            exp_timestamp = decoded.get("exp")
            if exp_timestamp:
                return datetime.utcfromtimestamp(exp_timestamp)
            else:
                logger.warning("No expiration found in token, defaulting to 1 hour")
                return datetime.utcnow() + timedelta(hours=1)
        except Exception as e:
            logger.warning(f"Could not parse token expiration: {e}, defaulting to 1 hour")
            return datetime.utcnow() + timedelta(hours=1)
    
    def _extract_user_id_from_token(self, access_token: str) -> Optional[str]:
        """Extract user ID from JWT token."""
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            return decoded.get("userId") or decoded.get("sub")
        except Exception as e:
            logger.warning(f"Could not extract user ID from token: {e}")
            return None
    
    async def get_valid_token(self) -> BouncieToken:
        """Get a valid token, refreshing if necessary."""
        if not self.current_token:
            raise Exception("No token available. Please authenticate first.")
        
        if self.current_token.needs_refresh:
            logger.info("Token needs refresh, attempting refresh...")
            try:
                return await self.refresh_token()
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                raise Exception("Token refresh failed. Please re-authenticate.")
        
        return self.current_token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.current_token:
            raise Exception("No token available")
        
        # Bouncie uses custom auth format (no Bearer prefix)
        return {
            "Authorization": self.current_token.access_token,
            "Content-Type": "application/json",
            "User-Agent": settings.scraping.user_agent
        }
    
    async def start_auto_refresh(self) -> None:
        """Start background token refresh task."""
        if self._refresh_task and not self._refresh_task.done():
            logger.warning("Auto refresh already running")
            return
        
        async def refresh_loop():
            logger.info(f"Started auto refresh task (checking every {self.config.auto_refresh_interval_seconds}s)")
            while True:
                try:
                    if self.current_token and self.current_token.needs_refresh:
                        logger.info("Auto-refreshing token...")
                        await self.refresh_token()
                    await asyncio.sleep(self.config.auto_refresh_interval_seconds)
                except Exception as e:
                    logger.error(f"Auto refresh error: {e}")
                    await asyncio.sleep(self.config.auto_refresh_interval_seconds)
        
        self._refresh_task = asyncio.create_task(refresh_loop())
    
    async def stop_auto_refresh(self) -> None:
        """Stop background token refresh task."""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped auto refresh task")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token."""
        return self.current_token is not None and not self.current_token.is_expired
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """Get current token information."""
        if not self.current_token:
            return None
        
        return {
            "user_id": self.current_token.user_id,
            "expires_at": self.current_token.expires_at.isoformat(),
            "expires_in_seconds": self.current_token.expires_in_seconds,
            "is_expired": self.current_token.is_expired,
            "needs_refresh": self.current_token.needs_refresh,
            "scope": self.current_token.scope,
            "created_at": self.current_token.created_at.isoformat()
        }

# ------------------------------ GLOBAL AUTH MANAGER INSTANCE ------------------------------

auth_manager = BouncieAuthManager()

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def get_bouncie_auth_headers() -> Dict[str, str]:
    """Get valid Bouncie authentication headers."""
    try:
        await auth_manager.get_valid_token()
        return auth_manager.get_auth_headers()
    except Exception as e:
        logger.error(f"Failed to get Bouncie auth headers: {e}")
        raise

def is_bouncie_authenticated() -> bool:
    """Check if Bouncie is authenticated."""
    return auth_manager.is_authenticated()

async def start_bouncie_auto_refresh() -> None:
    """Start Bouncie auto refresh task."""
    await auth_manager.start_auto_refresh()

async def stop_bouncie_auto_refresh() -> None:
    """Stop Bouncie auto refresh task."""
    await auth_manager.stop_auto_refresh()

# ------------------------------ END OF FILE ------------------------------
