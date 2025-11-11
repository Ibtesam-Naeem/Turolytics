# ------------------------------ SESSION HELPERS ------------------------------
from typing import Optional
import json
import tempfile
from datetime import datetime, timedelta
from playwright.async_api import BrowserContext

from core.utils.logger import logger
from core.config.settings import TIMEOUT_SHORT_CHECK, DELAY_VERY_LONG, settings
from core.database import SessionLocal
from core.database.models import Account, SessionStorage
from core.database.db_service import DatabaseService

async def _element_exists(page, selector: str, timeout: int = TIMEOUT_SHORT_CHECK) -> bool:
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
        await page.wait_for_timeout(DELAY_VERY_LONG) 
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

async def save_storage_state(context: BrowserContext, account_id: int = None) -> Optional[str]:
    """Save browser storage state to database only."""
    if not account_id:
        return None
        
    try:
        storage_state = await context.storage_state()
        storage_state_json = json.dumps(storage_state)
        
        try:
            db = SessionLocal()
            try:
                account = DatabaseService.get_account_by_id(db, account_id)
                if not account:
                    account = Account(account_id=account_id)
                    db.add(account)
                    db.commit()
                    db.refresh(account)
                
                session_storage = db.query(SessionStorage).filter(SessionStorage.account_id == account.id).first()
                if not session_storage:
                    session_storage = SessionStorage(account_id=account.id)
                    db.add(session_storage)
                
                session_storage.storage_state = storage_state_json
                expires_at = datetime.utcnow() + timedelta(hours=settings.scraping.session_expiry_hours)
                session_storage.expires_at = expires_at
                
                db.commit()
                logger.info(f"Session storage saved to database for account {account_id}")
                return str(account_id)
            
            except Exception as e:
                logger.error(f"Error saving session storage to database: {e}")
                db.rollback()
                return None
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Could not save session storage to database: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to save storage state: {e}")
        return None

def get_storage_state(account_id: int = None) -> Optional[str]:
    """Get storage state from database and save to temporary file for Playwright."""
    if not account_id:
        return None
    
    try:
        db = SessionLocal()
        try:
            account = DatabaseService.get_account_by_id(db, account_id)
            if not account:
                logger.info(f"No account found for account_id {account_id}")
                return None
            
            logger.debug(f"Found account {account_id} (DB ID: {account.id})")
            
            session_storage = db.query(SessionStorage).filter(
                SessionStorage.account_id == account.id
            ).first()
            
            if not session_storage:
                logger.info(f"No session storage record found for account {account_id}")
                return None
            
            if not session_storage.storage_state:
                logger.info(f"Session storage exists but storage_state is empty for account {account_id}")
                return None
            
            logger.debug(f"Found session storage for account {account_id}, expires_at: {session_storage.expires_at}")
            
            if session_storage.expires_at:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                expires_at = session_storage.expires_at
                
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                else:
                    expires_at = expires_at.astimezone(timezone.utc)
                
                if expires_at < now:
                    logger.info(f"Session expired for account {account_id} (expired at {expires_at}, now is {now})")
                    return None
                logger.debug(f"Session not expired (expires at {expires_at}, now is {now})")
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            temp_file.write(session_storage.storage_state)
            temp_file.flush()
            temp_file.close()
            
            logger.info(f"Retrieved session storage from database for account {account_id} - temp file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error retrieving session storage from database: {e}")
            return None
        
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------
