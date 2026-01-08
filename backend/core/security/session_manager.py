# ------------------------------ IMPORTS ------------------------------
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from starlette.requests import Request
import logging

from core.database.models import UserSession, Account
from core.config.settings import settings

logger = logging.getLogger(__name__)

def hash_token(token: str) -> str:
    """Hash a JWT token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()

def parse_user_agent(user_agent: Optional[str]) -> dict:
    """Parse user agent string to extract device info."""
    if not user_agent:
        return {
            "device_type": "Unknown",
            "browser": "Unknown",
            "os": "Unknown"
        }
    
    user_agent_lower = user_agent.lower()
    
    # Device type
    device_type = "desktop"
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        device_type = "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        device_type = "tablet"
    
    # Browser
    browser = "Unknown"
    if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
        browser = "Chrome"
    elif "firefox" in user_agent_lower:
        browser = "Firefox"
    elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
        browser = "Safari"
    elif "edg" in user_agent_lower:
        browser = "Edge"
    elif "opera" in user_agent_lower:
        browser = "Opera"
    
    # OS
    os_name = "Unknown"
    if "windows" in user_agent_lower:
        os_name = "Windows"
    elif "mac" in user_agent_lower or "darwin" in user_agent_lower:
        os_name = "macOS"
    elif "linux" in user_agent_lower:
        os_name = "Linux"
    elif "android" in user_agent_lower:
        os_name = "Android"
    elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
        os_name = "iOS"
    
    return {
        "device_type": device_type,
        "browser": browser,
        "os": os_name
    }

def create_or_update_session(
    db: Session,
    account: Account,
    token: str,
    request: Optional[Request] = None,
    expires_delta: Optional[timedelta] = None
) -> UserSession:
    """Create or update a user session."""
    token_hash = hash_token(token)
    
    # Check if session already exists
    session = db.query(UserSession).filter(
        UserSession.session_token_hash == token_hash,
        UserSession.account_id == account.id
    ).first()
    
    expires_at = None
    if expires_delta:
        expires_at = datetime.now(timezone.utc) + expires_delta
    else:
        # Default to token expiry (24 hours typically)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.security.access_token_expire_minutes)
    
    user_agent = None
    ip_address = None
    device_info = {}
    
    if request:
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        device_info = parse_user_agent(user_agent)
    
    if session:
        # Update existing session
        session.last_used_at = datetime.now(timezone.utc)
        session.expires_at = expires_at
        if user_agent:
            session.user_agent = user_agent
        if ip_address:
            session.ip_address = ip_address
        if device_info:
            session.device_type = device_info.get("device_type")
            session.browser = device_info.get("browser")
            session.os = device_info.get("os")
    else:
        # Create new session
        session = UserSession(
            account_id=account.id,
            session_token_hash=token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            device_type=device_info.get("device_type"),
            browser=device_info.get("browser"),
            os=device_info.get("os"),
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=1
        )
        db.add(session)
    
    try:
        db.commit()
        db.refresh(session)
        logger.info(f"Session {'created' if not session.id else 'updated'} for account {account.id}, session ID: {session.id}")
        return session
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit session to database: {e}", exc_info=True)
        raise

def get_user_sessions(db: Session, account: Account, current_token_hash: Optional[str] = None) -> list[UserSession]:
    """Get all active sessions for a user."""
    sessions = db.query(UserSession).filter(
        UserSession.account_id == account.id,
        UserSession.is_active == 1
    ).order_by(UserSession.last_used_at.desc()).all()
    
    # Update last_used_at for current session if provided
    if current_token_hash:
        current_session = next((s for s in sessions if s.session_token_hash == current_token_hash), None)
        if current_session:
            current_session.last_used_at = datetime.now(timezone.utc)
            db.commit()
    
    return sessions

def revoke_session(db: Session, account: Account, session_id: int) -> bool:
    """Revoke a specific session."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.account_id == account.id
    ).first()
    
    if not session:
        return False
    
    session.is_active = 0
    db.commit()
    return True

def revoke_all_other_sessions(db: Session, account: Account, current_token_hash: str) -> int:
    """Revoke all sessions except the current one."""
    count = db.query(UserSession).filter(
        UserSession.account_id == account.id,
        UserSession.session_token_hash != current_token_hash,
        UserSession.is_active == 1
    ).update({"is_active": 0})
    
    db.commit()
    return count

def revoke_all_sessions(db: Session, account: Account) -> int:
    """Revoke all sessions for a user."""
    count = db.query(UserSession).filter(
        UserSession.account_id == account.id,
        UserSession.is_active == 1
    ).update({"is_active": 0})
    
    db.commit()
    return count

