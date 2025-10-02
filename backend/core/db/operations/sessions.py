# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from core.db.base import Session, Account
from core.db.database import get_db_session
from core.config.settings import settings

logger = logging.getLogger(__name__)

# ------------------------------ SESSION OPERATIONS ------------------------------

def create_session(account_id: int, session_id: str, storage_state: dict, user_agent: str = None, ip_address: str = None) -> Optional[Session]:
    """Create a new browser session.
    
    Args:
        account_id: Account ID to associate session with.
        session_id: Unique session identifier.
        storage_state: Playwright storage state data.
        user_agent: User agent string used for the session.
        ip_address: IP address of the session.
        
    Returns:
        Session object if created successfully, None otherwise.
    """
    try:
        with get_db_session() as db:
            existing_sessions = db.query(Session).filter(
                Session.account_id == account_id,
                Session.is_active == True
            ).all()
            
            for session in existing_sessions:
                session.is_active = False
            
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.scraping.session_expiry_hours)
            
            new_session = Session(
                account_id=account_id,
                session_id=session_id,
                storage_state=storage_state,
                is_active=True,
                expires_at=expires_at,
                last_used_at=datetime.now(timezone.utc),
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            logger.info(f"Created new session {session_id} for account {account_id}")
            return new_session
            
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def get_active_session(account_id: int) -> Optional[Session]:
    """Get the most recent active session for an account.
    
    Args:
        account_id: Account ID to get session for.
        
    Returns:
        Active Session object if found, None otherwise.
    """
    try:
        with get_db_session() as db:
            session = db.query(Session).filter(
                Session.account_id == account_id,
                Session.is_active == True,
                Session.expires_at > datetime.now(timezone.utc)
            ).order_by(Session.last_used_at.desc()).first()
            
            if session:
                session.last_used_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(session)
                logger.info(f"Retrieved active session for account {account_id}")
            
            return session
            
    except Exception as e:
        logger.error(f"Error getting active session: {e}")
        return None

def get_active_session_storage_state(account_id: int) -> Optional[dict]:
    """Get storage state from the most recent active session for an account.
    
    Args:
        account_id: Account ID to get session for.
        
    Returns:
        Storage state dictionary if found, None otherwise.
    """
    try:
        with get_db_session() as db:
            session = db.query(Session).filter(
                Session.account_id == account_id,
                Session.is_active == True,
                Session.expires_at > datetime.now(timezone.utc)
            ).order_by(Session.last_used_at.desc()).first()
            
            if session:
                session.last_used_at = datetime.now(timezone.utc)
                db.commit()
                
                storage_state = session.storage_state
                logger.info(f"Retrieved storage state from database for account {account_id}")
                return storage_state
            else:
                logger.warning(f"No active session found for account {account_id}")
                return None
            
    except Exception as e:
        logger.error(f"Error getting active session storage state: {e}")
        return None

def update_session_usage(session_id: str) -> bool:
    """Update the last used timestamp for a session.
    
    Args:
        session_id: Session ID to update.
        
    Returns:
        True if updated successfully, False otherwise.
    """
    try:
        with get_db_session() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if session:
                session.last_used_at = datetime.now(timezone.utc)
                db.commit()
                logger.debug(f"Updated usage for session {session_id}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error updating session usage: {e}")
        return False

def deactivate_session(session_id: str) -> bool:
    """Deactivate a session.
    
    Args:
        session_id: Session ID to deactivate.
        
    Returns:
        True if deactivated successfully, False otherwise.
    """
    try:
        with get_db_session() as db:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if session:
                session.is_active = False
                db.commit()
                logger.info(f"Deactivated session {session_id}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error deactivating session: {e}")
        return False

def cleanup_expired_sessions() -> int:
    """Clean up expired sessions.
    
    Returns:
        Number of sessions cleaned up.
    """
    try:
        with get_db_session() as db:
            expired_sessions = db.query(Session).filter(
                Session.expires_at < datetime.now(timezone.utc)
            ).all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                session.is_active = False
            
            db.commit()
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        return 0

# ------------------------------ END OF FILE ------------------------------
