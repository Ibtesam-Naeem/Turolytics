# ------------------------------ SESSION HELPERS ------------------------------
from typing import Optional, Dict, Any
from datetime import datetime

from core.utils.logger import logger

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

async def save_storage_state(context, account_id: int = None, user_agent: str = None, 
                           ip_address: str = None) -> Optional[str]:
    """Save storage state - placeholder for future implementation."""
    # Database storage removed - implement file-based storage if needed
    return None

def get_storage_state(account_id: int = None) -> Optional[Dict[str, Any]]:
    """Get storage state - placeholder for future implementation."""
    # Database storage removed - implement file-based storage if needed
    return None

# ------------------------------ END OF FILE ------------------------------
