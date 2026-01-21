# ------------------------------ IMPORTS ------------------------------
import hmac
import hashlib
import time
from typing import Optional
from fastapi import Request, HTTPException, status

from core.config.settings import settings

# ------------------------------ CONSTANTS ------------------------------

SESSION_COOKIE_NAME = "waitlist_admin_session"
SESSION_DURATION = 86400  # 24 hours in seconds

def generate_session_token() -> str:
    """Generate a secure session token."""
    timestamp = str(int(time.time()))
    message = f"{timestamp}:{settings.waitlist_admin.session_secret}"
    token = hmac.new(
        settings.waitlist_admin.session_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{timestamp}:{token}"

def verify_session_token(token: str) -> bool:
    """Verify a session token is valid and not expired."""
    try:
        parts = token.split(":", 1)
        if len(parts) != 2:
            return False
        
        timestamp_str, token_hash = parts
        timestamp = int(timestamp_str)
        
        if time.time() - timestamp > SESSION_DURATION:
            return False
        
        message = f"{timestamp_str}:{settings.waitlist_admin.session_secret}"
        expected_hash = hmac.new(
            settings.waitlist_admin.session_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(token_hash, expected_hash)
    except (ValueError, AttributeError):
        return False

def get_session_from_request(request: Request) -> Optional[str]:
    """Get session token from request (cookie or header)."""
    # Try cookie first
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token and verify_session_token(cookie_token):
        return cookie_token
    
    # Try Authorization header as fallback
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if verify_session_token(token):
            return token
    
    return None

def require_waitlist_auth(request: Request) -> bool:
    """Dependency to require waitlist admin authentication."""
    session_token = get_session_from_request(request)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return True

# ------------------------------ END OF FILE ------------------------------
