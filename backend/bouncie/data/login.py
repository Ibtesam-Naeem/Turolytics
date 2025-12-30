# ------------------------------ IMPORTS ------------------------------
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse, parse_qs

from playwright.async_api import Page, BrowserContext, Browser
from core.config.browser_settings import launch_browser
from core.config.settings import settings, TIMEOUT_SELECTOR_WAIT, TIMEOUT_QUICK_CHECK, DELAY_SHORT, DELAY_MEDIUM, DELAY_VERY_LONG, DELAY_PAGE_LOAD, DELAY_FORM_SUBMIT

from .selectors import (
    BOUNCIE_LOGIN_URL,
    EMAIL_SELECTOR,
    PASSWORD_SELECTOR,
    SIGN_IN_BUTTON_SELECTOR,
    AUTHORIZE_BUTTON_SELECTOR,
    AUTHORIZATION_SUCCESS_URL_PATTERN,
    ERROR_SELECTOR
)

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def check_login_success(page: Page) -> bool:
    """Check if login was successful by looking for authorization page or dashboard."""
    try:
        # Check if we're on the authorization page (after successful login)
        current_url = page.url
        if "auth.bouncie.com/dialog/authorize" in current_url:
            logger.info("Login successful! On authorization page.")
            return True
        
        # Check if we're redirected to dashboard or account page
        if "dashboard" in current_url or "account" in current_url:
            logger.info("Login successful! Redirected to dashboard.")
            return True
        
        # Check for authorize button (indicates we're on authorization page)
        try:
            authorize_button = await page.wait_for_selector(AUTHORIZE_BUTTON_SELECTOR, timeout=2000)
            if authorize_button:
                logger.info("Login successful! Found authorize button.")
                return True
        except:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Error checking login success: {e}")
        return False

async def login_with_credentials(page: Page, email: str, password: str) -> bool:
    """Login with credentials, fill form, and submit."""
    try:
        if not email or not password:
            raise Exception("Bouncie credentials are required. Please provide email and password.")
        
        logger.info("Navigating to Bouncie login page...")
        await page.goto(BOUNCIE_LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(DELAY_PAGE_LOAD)
        
        for attempt in range(settings.scraping.retry_attempts):
            logger.info(f"Login attempt {attempt + 1}/{settings.scraping.retry_attempts}")
            
            # Wait for and fill email
            logger.info("Filling in email...")
            email_input = await page.wait_for_selector(EMAIL_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
            await email_input.clear()
            await email_input.fill(email)
            await page.wait_for_timeout(DELAY_SHORT)
            
            # Wait for and fill password
            logger.info("Filling in password...")
            password_input = await page.wait_for_selector(PASSWORD_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
            await password_input.clear()
            await password_input.fill(password)
            await page.wait_for_timeout(DELAY_MEDIUM)
            
            # Click sign in button
            logger.info("Clicking sign in button...")
            sign_in_button = await page.wait_for_selector(SIGN_IN_BUTTON_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
            await sign_in_button.click()
            await page.wait_for_timeout(DELAY_VERY_LONG)
            
            # Check for errors
            try:
                error_element = await page.wait_for_selector(ERROR_SELECTOR, timeout=2000)
                if error_element:
                    error_text = await error_element.text_content()
                    logger.error(f"Login failed with error: '{error_text}'")
                    if attempt < settings.scraping.retry_attempts - 1:
                        logger.warning(f"Retrying login (Attempt {attempt + 2}/{settings.scraping.retry_attempts})...")
                    continue
            except:
                # No error found, continue
                pass
            
            # Check if login was successful
            if await check_login_success(page):
                logger.info("Login successful!")
                return True
            
            # If we're still on login page, there might be an error
            if "login" in page.url.lower():
                logger.warning("Still on login page after submit. May have failed.")
                if attempt < settings.scraping.retry_attempts - 1:
                    logger.warning(f"Retrying login (Attempt {attempt + 2}/{settings.scraping.retry_attempts})...")
                continue
        
        logger.error("All login attempts failed.")
        return False
        
    except Exception as e:
        logger.exception(f"Error during login_with_credentials: {e}")
        return False

async def authorize_application(page: Page) -> Optional[str]:
    """
    Click the 'Authorize Access' button and extract the authorization code from the redirect URL.
    
    Returns:
        Authorization code if successful, None otherwise
    """
    try:
        logger.info("Waiting for authorize button...")
        
        # Wait for authorize button to appear
        authorize_button = await page.wait_for_selector(AUTHORIZE_BUTTON_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
        if not authorize_button:
            logger.error("Authorize button not found")
            return None
        
        logger.info("Clicking 'Authorize Access' button...")
        
        # Set up a promise to wait for navigation
        async with page.expect_response(lambda response: "callback" in response.url or "code=" in response.url, timeout=30000) as response_info:
            await authorize_button.click()
        
        # Wait a bit for redirect
        await page.wait_for_timeout(DELAY_VERY_LONG)
        
        # Check current URL for authorization code
        current_url = page.url
        logger.info(f"Current URL after authorization: {current_url}")
        
        # Extract code from URL
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            logger.info(f"Authorization code extracted: {auth_code[:20]}...")
            return auth_code
        else:
            logger.warning(f"No authorization code found in URL: {current_url}")
            return None
            
    except Exception as e:
        logger.exception(f"Error during authorize_application: {e}")
        return None

# ------------------------------ COMPLETE LOGIN FLOW ------------------------------

async def complete_bouncie_login(
    email: str,
    password: str,
    authorization_url: str,
    headless: bool = None
) -> Optional[Dict[str, Any]]:
    """
    Complete Bouncie login and authorization flow.
    
    Args:
        email: Bouncie account email
        password: Bouncie account password
        authorization_url: OAuth authorization URL (from BouncieService.get_authorization_url())
        headless: Whether to run browser in headless mode
    
    Returns:
        Dict with authorization_code if successful, None otherwise
    """
    browser = None
    try:
        if headless is None:
            headless = settings.scraping.headless
        
        logger.info("Initiating Bouncie login automation...")
        page, context, browser = await launch_browser(headless=headless, storage_state_path=None)
        
        # Step 1: Login with credentials
        if not await login_with_credentials(page, email, password):
            logger.error("Failed to login with credentials")
            return None
        
        # Step 2: Navigate to authorization URL (if not already there)
        current_url = page.url
        if "auth.bouncie.com/dialog/authorize" not in current_url:
            logger.info("Navigating to authorization URL...")
            await page.goto(authorization_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(DELAY_PAGE_LOAD)
        
        # Step 3: Click authorize button and extract code
        auth_code = await authorize_application(page)
        
        if not auth_code:
            logger.error("Failed to get authorization code")
            return None
        
        logger.info("Bouncie login and authorization completed successfully")
        
        return {
            "success": True,
            "authorization_code": auth_code,
            "message": "Login and authorization successful"
        }
        
    except Exception as e:
        logger.exception(f"Error in complete_bouncie_login: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Error during browser cleanup: {e}")

# ------------------------------ END OF FILE ------------------------------

