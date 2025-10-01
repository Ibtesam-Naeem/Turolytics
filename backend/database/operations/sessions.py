# ------------------------------ IMPORTS ------------------------------
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TypedDict
from sqlalchemy import and_, or_

from ..config import SessionLocal
from ..models import Session as SessionModel, Account
from utils.logger import logger

# ------------------------------ TYPE DEFINITIONS ------------------------------

class SessionData(TypedDict):
    """Typed dictionary for session data structure."""
    id: int
    session_id: str
    account_id: int
    storage_state: Dict[str, Any]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: datetime
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime

# ------------------------------ SESSION MANAGEMENT ------------------------------

def create_session(account_id: int, storage_state: Dict[str, Any], 
                  user_agent: str = None, ip_address: str = None,
                  expires_hours: int = 24) -> Optional[SessionData]:
    """Create a new session in the database."""
    db = SessionLocal()
    try:
        # Ensure account exists
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            logger.error(f"Account with ID {account_id} not found.")
            return None

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Create session record
        now = datetime.utcnow()
        session = SessionModel(
            account_id=account_id,
            session_id=session_id,
            storage_state=storage_state,
            is_active=True,
            expires_at=expires_at,
            last_used_at=now,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            updated_at=now
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)  # Ensure all fields are populated
        
        logger.info(f"Created session {session_id} for account {account_id}")
        
        # Return consistent SessionData structure
        return {
            'id': session.id,
            'session_id': session.session_id,
            'account_id': session.account_id,
            'storage_state': session.storage_state,
            'is_active': session.is_active,
            'expires_at': session.expires_at,
            'last_used_at': session.last_used_at,
            'user_agent': session.user_agent,
            'ip_address': session.ip_address,
            'created_at': session.created_at,
            'updated_at': session.updated_at
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def get_session(session_id: str) -> Optional[SessionData]:
    """Retrieve an active session by ID."""
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.session_id == session_id,
                SessionModel.is_active == True,
                or_(
                    SessionModel.expires_at.is_(None),
                    SessionModel.expires_at > datetime.utcnow()
                )
            )
        ).first()
        
        if session:
            # Update timestamps
            now = datetime.utcnow()
            session.last_used_at = now
            session.updated_at = now
            db.commit()
            logger.info(f"Retrieved session {session_id}")
            
            # Return session data as dictionary
            return {
                'id': session.id,
                'session_id': session.session_id,
                'account_id': session.account_id,
                'storage_state': session.storage_state,
                'is_active': session.is_active,
                'expires_at': session.expires_at,
                'last_used_at': session.last_used_at,
                'user_agent': session.user_agent,
                'ip_address': session.ip_address,
                'created_at': session.created_at,
                'updated_at': session.updated_at
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        return None
    finally:
        db.close()


def get_storage_state_for_account(account_id: int) -> Optional[SessionData]:
    """Get the most recent active storage state for an account."""
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(
            and_(
                SessionModel.account_id == account_id,
                SessionModel.is_active == True,
                or_(
                    SessionModel.expires_at.is_(None),
                    SessionModel.expires_at > datetime.utcnow()
                )
            )
        ).order_by(SessionModel.last_used_at.desc()).first()
        
        if session:
            # Update timestamps
            now = datetime.utcnow()
            session.last_used_at = now
            session.updated_at = now
            db.commit()
            logger.info(f"Retrieved storage state for account {account_id}")
            
            # Return consistent session data structure
            return {
                'id': session.id,
                'session_id': session.session_id,
                'account_id': session.account_id,
                'storage_state': session.storage_state,
                'is_active': session.is_active,
                'expires_at': session.expires_at,
                'last_used_at': session.last_used_at,
                'user_agent': session.user_agent,
                'ip_address': session.ip_address,
                'created_at': session.created_at,
                'updated_at': session.updated_at
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting storage state for account {account_id}: {e}")
        return None
    finally:
        db.close()