# ------------------------------ SESSION HELPERS ------------------------------
from typing import Optional
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from playwright.async_api import BrowserContext
import logging

from core.config.settings import TIMEOUT_SHORT_CHECK, DELAY_VERY_LONG, settings
from core.database import SessionLocal
from core.database.models import SessionStorage
from core.database.db_service import DatabaseService

logger = logging.getLogger(__name__)

async def _element_exists(page, selector: str, timeout: int = TIMEOUT_SHORT_CHECK) -> bool:
    """Check if an element exists on the page within timeout."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False

async def verify_session_authenticated(page):
    """Check if current storage state is authenticated using multiple verification methods.
    
    Navigates to business earnings page (host-specific) to verify authentication.
    This ensures we're checking a host account page, not the main public site.
    """
    try:
        # Navigate to business earnings page (host-specific) to verify auth
        # This is better than going to main site or trips page
        await page.goto("https://turo.com/us/en/business/earnings", wait_until="domcontentloaded")
        await page.wait_for_timeout(DELAY_VERY_LONG)
        current_url = page.url
        
        # Check if we're on a login page (redirected due to invalid session)
        if "login" in current_url.lower() or "signin" in current_url.lower():
            return False
        
        # Check if we're on the business earnings page (indicates authenticated host account)
        if "business/earnings" in current_url or "business" in current_url:
            # Check for authentication indicators
            auth_selectors = [
                '[data-testid="user-menu"]', '.user-menu', '.account-menu',
                '[aria-label*="Account"]', '[aria-label*="Profile"]',
                '.avatar', '.user-avatar', '.host-dashboard-title',
                '[data-testid="host-dashboard"]', '.host-dashboard',
                '[data-testid="earningsFilterSummary"]', '.earnings',
                '[data-testid="earnings"]', '.business-earnings'
            ]
            
            for selector in auth_selectors:
                if await _element_exists(page, selector, 2000):
                    return True
        
        # Check for login form elements (indicates not authenticated)
        login_selectors = [
            'input[type="email"]', 'input[name="email"]', '#email',
            '.login-form', '[data-testid="login-form"]',
            'button[type="submit"]', '.submit-button'
        ]
        
        for selector in login_selectors:
            if await _element_exists(page, selector, 1000):
                return False
        
        # If we're on a business/host page and not on login, assume authenticated
        if "business" in current_url or "host" in current_url:
            return True
        
        return False

    except Exception as e:
        logger.warning(f"Session verification failed: {e}")
        return False

async def save_storage_state(context: BrowserContext, account_id: int = None, email: str = None) -> Optional[str]:
    """
    Save browser storage state to database only.
    
    Note: account_id parameter is the actual user_id (hash-based identifier).
    If account doesn't exist and email is provided, it will be created.
    """
    if not account_id:
        return None
        
    try:
        storage_state = await context.storage_state()
        storage_state_json = json.dumps(storage_state)
        
        db = SessionLocal()
        try:
            account = DatabaseService.get_account_by_user_id(db, account_id)
            
            if not account:
                if email:
                    account = DatabaseService.get_or_create_account(db, account_id, email)
                    logger.info(f"Created account for user_id {account_id} when saving session")
                else:
                    logger.warning(f"Account with user_id {account_id} not found when saving session and no email provided")
                    return None
            
            session_storage = db.query(SessionStorage).filter(SessionStorage.account_id == account.id).first()
            
            if not session_storage:
                session_storage = SessionStorage(account_id=account.id)
                db.add(session_storage)
            
            session_storage.storage_state = storage_state_json
            session_storage.expires_at = datetime.utcnow() + timedelta(hours=settings.scraping.session_expiry_hours)
            
            db.commit()
            logger.info(f"Session storage saved for user {account_id}")
            return str(account_id)
        
        except Exception as e:
            logger.error(f"Error saving session storage: {e}")
            db.rollback()
            return None
        
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to save storage state: {e}")
        return None

def get_storage_state(account_id: int = None) -> Optional[str]:
    """
    Get storage state from database and save to temporary file for use in Playwright.
    
    Note: account_id parameter is the actual user_id (hash-based identifier).
    """
    if not account_id:
        return None
    
    try:
        db = SessionLocal()
        try:
            account = DatabaseService.get_account_by_user_id(db, account_id)
            if not account:
                return None
            
            session_storage = db.query(SessionStorage).filter(
                SessionStorage.account_id == account.id
            ).first()
            
            if not session_storage or not session_storage.storage_state:
                return None
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            temp_file.write(session_storage.storage_state)
            temp_file.flush()
            temp_file.close()
            
            os.chmod(temp_file.name, 0o600)
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error retrieving session storage: {e}")
            return None
        
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def cleanup_storage_state_file(file_path: Optional[str]) -> None:
    """Safely delete a storage state temp file."""
    if not file_path:
        return
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temp storage state file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# ------------------------------ END OF FILE ------------------------------
