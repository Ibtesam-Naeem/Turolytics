# ------------------------------ SESSION HELPERS ------------------------------
from typing import Optional, Dict, Any
from datetime import datetime

from core.utils.logger import logger
from core.config.settings import settings
from core.db.operations.sessions import (
    create_session, get_active_session, update_session_usage, 
    deactivate_session, get_active_session_storage_state
)

async def _element_exists(page, selector: str, timeout: int = 2000) -> bool:
    """Check if an element exists on the page within timeout."""
    try:
        element = await page.wait_for_selector(selector, timeout=timeout)
        return element is not None
        
    except Exception:
        return False

async def verify_session_authenticated(page):
    """Check if current storage state is authenticated using multiple verification methods."""
    try:
        logger.info("Verifying session authentication...")
        
        await page.goto("https://turo.com/ca/en/trips/booked", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000) 
        current_url = page.url
        if "login" in current_url or "signin" in current_url:
            logger.info("Session invalid - redirected to login page")
            return False
        
        if "trips" not in current_url:
            logger.info(f"Session invalid - not on trips page, current URL: {current_url}")
            return False
        
        auth_selectors = [
            '[data-testid="user-menu"]', '.user-menu', '.account-menu',
            '[aria-label*="Account"]', '[aria-label*="Profile"]',
            '.avatar', '.user-avatar', '.host-dashboard-title',
            '[data-testid="host-dashboard"]', '.host-dashboard',
            '[data-testid="trips-page"]', '.trips-container'
        ]
        
        for selector in auth_selectors:
            if await _element_exists(page, selector, 3000):
                logger.info(f"Session restore successful - Found auth element: {selector}")
                return True
        
        login_selectors = [
            'input[type="email"]', 'input[name="email"]', '#email',
            '.login-form', '[data-testid="login-form"]',
            'button[type="submit"]', '.submit-button'
        ]
        
        for selector in login_selectors:
            if await _element_exists(page, selector, 1000):
                logger.info("Session invalid - login form detected")
                return False
        
        user_content_selectors = [
            '.user-name', '.account-name', '.profile-name',
            '[data-testid="user-info"]', '.host-info'
        ]
        
        for selector in user_content_selectors:
            if await _element_exists(page, selector, 1000):
                logger.info(f"Session restore successful - Found user content: {selector}")
                return True
        
        logger.info("Session restore successful - URL verification passed")
        return True

    except Exception as e:
        logger.warning(f"Session verification failed: {e}")
        return False

async def save_storage_state_to_db(context, account_id: int, user_agent: str = None, 
                                 ip_address: str = None) -> Optional[str]:
    """Save current context storage state to database."""
    try:
        storage_state = await context.storage_state()
        
        import uuid
        session_id = str(uuid.uuid4())
        
        session = create_session(
            account_id=account_id,
            session_id=session_id,
            storage_state=storage_state,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        if session:
            logger.info(f"Saved session storage state to database: {session_id}")
            return session_id
        else:
            logger.error("Failed to save session to database")
            return None
            
    except Exception as e:
        logger.error(f"Error saving storage state to database: {e}")
        return None

async def save_storage_state(context, account_id: int = None, user_agent: str = None, 
                           ip_address: str = None) -> Optional[str]:
    """Save storage state to database only."""
    if account_id:
        return await save_storage_state_to_db(
            context, account_id, user_agent, ip_address
        )
    
    return None

def get_storage_state_from_db(account_id: int) -> Optional[Dict[str, Any]]:
    """Get storage state from database for an account."""
    try:
        storage_state = get_active_session_storage_state(account_id)
        if storage_state:
            logger.info(f"Retrieved storage state from database for account {account_id}")
            return storage_state
        else:
            logger.warning(f"No storage state found for account {account_id}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving storage state from database: {e}")
        return None

def get_storage_state(account_id: int = None) -> Optional[Dict[str, Any]]:
    """Get storage state from database only."""
    if account_id:
        return get_storage_state_from_db(account_id)
    
    return None

# ------------------------------ END OF FILE ------------------------------
