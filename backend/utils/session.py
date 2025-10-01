# ------------------------------ SESSION HELPERS ------------------------------
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from utils.logger import logger
from config.settings import settings
from database.operations.sessions import (
    create_session, get_session, get_storage_state_for_account
)

def get_storage_state_path(account_id: int = None):
    """Return absolute path to Playwright storage state JSON (legacy fallback)."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    session_dir = os.path.join(base_dir, "session")
    os.makedirs(session_dir, exist_ok=True)
    
    if account_id:
        return os.path.join(session_dir, f"turo_storage_state_account_{account_id}.json")
    else:
        return os.path.join(session_dir, "turo_storage_state.json")


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
        await page.goto("https://turo.com/ca/en/trips/booked", wait_until="domcontentloaded")
        await page.wait_for_timeout(800)
        
        if "trips" not in page.url:
            logger.info("Session invalid - not redirected to trips page")
            return False
        
        auth_selectors = [
            '[data-testid="user-menu"]', '.user-menu', '.account-menu',
            '[aria-label*="Account"]', '[aria-label*="Profile"]',
            '.avatar', '.user-avatar', '.host-dashboard-title',
            '[data-testid="host-dashboard"]'
        ]
        
        for selector in auth_selectors:
            if await _element_exists(page, selector, 2000):
                logger.info(f"Session restore successful - Found auth element: {selector}")
                return True
        
        login_selectors = [
            'input[type="email"]', 'input[name="email"]', '#email',
            '.login-form', '[data-testid="login-form"]'
        ]
        
        for selector in login_selectors:
            if await _element_exists(page, selector, 1000):
                logger.info("Session invalid - login form detected")
                return False
        
        logger.info("Session restore successful - URL verification passed")
        return True

    except Exception as e:
        logger.warning(f"Stored session invalid or expired: {e}")
        return False

async def save_storage_state_to_db(context, account_id: int, user_agent: str = None, 
                                 ip_address: str = None) -> Optional[str]:
    """Save current context storage state to database."""
    try:
        storage_state = await context.storage_state()
        
        session_data = create_session(
            account_id=account_id,
            storage_state=storage_state,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_hours=settings.scraping.session_expiry_hours
        )
        
        if session_data:
            logger.info(f"Saved session storage state to database: {session_data['session_id']}")
            return session_data['session_id']
        else:
            logger.error("Failed to save session to database")
            return None
            
    except Exception as e:
        logger.error(f"Error saving storage state to database: {e}")
        return None


async def save_storage_state_to_file(context, account_id: int = None) -> Optional[str]:
    """Save current context storage state to JSON file (legacy fallback)."""
    storage_path = get_storage_state_path(account_id)
    try:
        await context.storage_state(path=storage_path)
        logger.info(f"Saved session storage state to file: {storage_path}")
        return storage_path

    except Exception as e:
        logger.warning(f"Could not save storage state to file: {e}")
        return None


async def save_storage_state(context, account_id: int = None, user_agent: str = None, 
                           ip_address: str = None) -> Optional[str]:
    """Save storage state to database (preferred) or file (fallback)."""
    if account_id:
        session_id = await save_storage_state_to_db(
            context, account_id, user_agent, ip_address
        )
        if session_id:
            return session_id
    
    return await save_storage_state_to_file(context, account_id)


def get_storage_state_from_db(account_id: int) -> Optional[Dict[str, Any]]:
    """Get storage state from database for an account."""
    try:
        session_data = get_storage_state_for_account(account_id)
        if session_data:
            logger.info(f"Retrieved storage state from database for account {account_id}")
            return session_data['storage_state']
        else:
            logger.warning(f"No storage state found for account {account_id}")
            return None

    except Exception as e:
        logger.error(f"Error retrieving storage state from database: {e}")
        return None


def get_storage_state_from_file(account_id: int = None) -> Optional[Dict[str, Any]]:
    """Get storage state from JSON file (legacy fallback)."""
    storage_path = get_storage_state_path(account_id)
    try:
        if os.path.exists(storage_path):
            with open(storage_path, 'r') as f:
                storage_state = json.load(f)
                logger.info(f"Retrieved storage state from file: {storage_path}")
                return storage_state

    except Exception as e:
        logger.warning(f"Could not load storage state from file: {e}")
    return None


def get_storage_state(account_id: int = None) -> Optional[Dict[str, Any]]:
    """Get storage state from database (preferred) or file (fallback)."""
    if account_id:
        storage_state = get_storage_state_from_db(account_id)
        if storage_state:
            return storage_state
    
    return get_storage_state_from_file(account_id)

# ------------------------------ END OF FILE ------------------------------

