# ------------------------------ IMPORTS ------------------------------
from typing import Optional, Tuple, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone

from playwright.async_api import Page, BrowserContext, Browser
import logging

from core.config.browser_settings import launch_browser

logger = logging.getLogger(__name__)
from core.config.settings import settings, TIMEOUT_SELECTOR_WAIT, TIMEOUT_IFRAME, TIMEOUT_QUICK_CHECK, TIMEOUT_SHORT_CHECK, DELAY_SHORT, DELAY_MEDIUM, DELAY_VERY_LONG, DELAY_PAGE_LOAD, DELAY_FORM_SUBMIT
from core.security.session import verify_session_authenticated, save_storage_state, get_storage_state
from .helpers import get_iframe_content, search_for_error_messages, clear_form_inputs, check_for_success_element, click_continue_button_with_retry
from .selectors import (
    LOGIN_URL, CONTINUE_WITH_EMAIL_SELECTOR, EMAIL_SELECTOR, PASSWORD_SELECTOR,
    TEXT_CODE_BUTTON, CODE_INPUT_SELECTOR, FINAL_CONTINUE_BUTTON, CONTINUE_BUTTON_TEXT_SELECTOR,
    LOGIN_SUCCESS_URLS, LOGIN_SUCCESS_SELECTORS
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def check_login_success(page: Page) -> bool:
    """Check if login was successful by looking for success indicators."""
    for indicator in LOGIN_SUCCESS_URLS:
        try:
            await page.wait_for_url(indicator, timeout=TIMEOUT_QUICK_CHECK)
            logger.info(f"Login successful! Redirected to: {indicator}")
            return True
        except:
            continue
    
    for selector in LOGIN_SUCCESS_SELECTORS:
        try:
            element = await page.wait_for_selector(selector, timeout=TIMEOUT_SHORT_CHECK)
            if element:
                logger.info(f"Login successful - Found success indicator: {selector}")
                return True
        except:
            continue
    
    return False

async def open_turo_login(page: Page) -> bool:
    """Open login page and click 'Continue with email'."""
    try:
        logger.info("Navigating to Turo login page...")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(DELAY_PAGE_LOAD)

        button = await page.wait_for_selector(CONTINUE_WITH_EMAIL_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
        if not button:
            return False

        await button.hover()
        await button.click()
        await page.wait_for_timeout(DELAY_FORM_SUBMIT)
        logger.info("'Continue with email' clicked successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during open_turo_login: {e}")
        return False

async def login_with_credentials(page: Page, email: str = None, password: str = None) -> bool:
    """Login with credentials, fill form, and submit."""
    try:
        if not email or not password:
            raise Exception("Turo credentials are required. Please provide email and password.")
        
        for attempt in range(settings.scraping.retry_attempts):
            logger.info("Switching to login iframe...")
            iframe_content = await get_iframe_content(page)
            if not iframe_content:
                logger.error("Could not access iframe content.")
                return False

            logger.info("Filling in login credentials...")
            email_input = await iframe_content.wait_for_selector(EMAIL_SELECTOR, timeout=TIMEOUT_IFRAME)
            password_input = await iframe_content.wait_for_selector(PASSWORD_SELECTOR, timeout=TIMEOUT_IFRAME)

            await email_input.fill(email)
            await page.wait_for_timeout(DELAY_SHORT)
            await password_input.fill(password)
            await page.wait_for_timeout(DELAY_MEDIUM)

            await click_continue_button_with_retry(page, iframe_content, CONTINUE_BUTTON_TEXT_SELECTOR)
            await page.wait_for_timeout(DELAY_VERY_LONG)

            error_message = await search_for_error_messages(page, iframe_content)
            if error_message:
                logger.error(f"Login failed with error: '{error_message}'")
                await clear_form_inputs(page, [EMAIL_SELECTOR, PASSWORD_SELECTOR], iframe_content)
                if attempt < settings.scraping.retry_attempts - 1:
                    logger.warning(f"Retrying login (Attempt {attempt + 2}/{settings.scraping.retry_attempts})...")
                continue

            if await check_for_success_element(page, [TEXT_CODE_BUTTON], iframe_content):
                logger.info("Login successful. Proceeding to 2FA.")
                return True
            
            logger.error("Login failed: No error message found and 2FA not triggered.")
            await clear_form_inputs(page, [EMAIL_SELECTOR, PASSWORD_SELECTOR], iframe_content)
            if attempt < settings.scraping.retry_attempts - 1:
                logger.warning(f"Retrying login (Attempt {attempt + 2}/{settings.scraping.retry_attempts})...")

        logger.error("All login attempts failed.")
        return False

    except Exception as e:
        logger.exception(f"Error during login_with_credentials: {e}")
        return False

async def prepare_two_factor_auth(page: Page) -> Tuple[bool, bool]:
    """
    Prepare for 2FA by clicking the text code button.
    Returns (success, is_main_page) where is_main_page indicates if 2FA is on main page or in iframe.
    """
    try:
        logger.info("Waiting for 2FA page...")

        try:
            text_button = await page.wait_for_selector(TEXT_CODE_BUTTON, timeout=TIMEOUT_QUICK_CHECK)
            await text_button.click()
            logger.info("'Text code' button clicked on main page.")
            return True, True
        except:
            try:
                iframe_content = await get_iframe_content(page, timeout=TIMEOUT_SELECTOR_WAIT)
                text_button = await iframe_content.wait_for_selector(TEXT_CODE_BUTTON, timeout=TIMEOUT_SELECTOR_WAIT)
                await text_button.click()
                logger.info("'Text code' button clicked in iframe.")
                return True, False

            except Exception as e:
                logger.error(f"Could not find 2FA text button: {e}")
                return False, False

    except Exception as e:
        logger.exception(f"Error during prepare_two_factor_auth: {e}")
        return False, False

async def submit_two_factor_auth(page: Page, code: str, is_main_page: bool = True) -> bool:
    """Submit 2FA code."""
    try:
        if not code:
            raise Exception("2FA code is required. Please provide the code.")

        if is_main_page:
            await page.fill(CODE_INPUT_SELECTOR, code)
            submit_btn = await page.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=TIMEOUT_SELECTOR_WAIT)
        else:
            iframe_content = await get_iframe_content(page, timeout=TIMEOUT_SELECTOR_WAIT)
            await iframe_content.fill(CODE_INPUT_SELECTOR, code)
            submit_btn = await iframe_content.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=TIMEOUT_SELECTOR_WAIT)

        await submit_btn.click()
        await page.wait_for_timeout(DELAY_VERY_LONG)
        logger.info("2FA code submitted successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during submit_two_factor_auth: {e}")
        return False

# ------------------------------ SHARED LOGIN HELPERS ------------------------------

async def _try_restore_session(account_id: int, headless: bool) -> Optional[Tuple[Page, BrowserContext, Browser]]:
    """Try to restore existing session. Returns (page, context, browser) if successful, None otherwise."""
    storage_state = get_storage_state(account_id)
    if not storage_state:
        return None
    
    logger.info(f"Found existing session for account {account_id}, attempting to restore...")
    page, context, browser = await launch_browser(
        headless=headless, 
        storage_state_path=storage_state  
    )
    
    if await verify_session_authenticated(page):
        logger.info("Session restored successfully - no login required")
        return page, context, browser
    else:
        logger.info("Existing session invalid, proceeding with fresh login")
        await browser.close()
        return None

async def _perform_credential_login(page: Page, email: str, password: str) -> bool:
    """Perform credential login with retries. Returns True if successful."""
    if not await open_turo_login(page):
        return False
    
    for attempt in range(settings.scraping.retry_attempts):
        if await login_with_credentials(page, email, password):
            return True
        if attempt < settings.scraping.retry_attempts - 1:
            logger.warning(f"Login attempt {attempt + 1} failed. Retrying...")
    
    logger.error("All login attempts failed.")
    return False

# ------------------------------ COMPLETE LOGIN FLOW (FOR SCRAPING) ------------------------------

async def complete_turo_login(account_id: int = 1, email: str = None, password: str = None, two_fa_code: str = None) -> Optional[Tuple[Page, BrowserContext, Browser]]:
    """Log into Turo using manual email/password and 2FA input, or restore existing session."""
    browser = None
    try:
        headless = settings.scraping.headless
        
        if not email or not password:
            raise Exception("Turo credentials are required. Please provide email and password.")
        
        restored = await _try_restore_session(account_id, headless)
        if restored:
            return restored
        
        logger.info("Initiating Turo login automation...")
        page, context, browser = await launch_browser(headless=headless, storage_state_path=None)
        
        if not await _perform_credential_login(page, email, password):
            return None

        if await check_for_success_element(page, [TEXT_CODE_BUTTON], iframe_content=None):
            if two_fa_code:
                success, is_main_page = await prepare_two_factor_auth(page)
                if not success or not await submit_two_factor_auth(page, two_fa_code, is_main_page):
                    return None
            else:
                logger.info("2FA required but no code provided - login session will be stored")
                return None

        if await check_login_success(page):
            logger.info("Login successful, user has been successfully authenticated.")
            await save_storage_state(context, account_id=account_id, email=email)
            return page, context, browser
        else:
            logger.error("Unable to confirm a successful login - no success indicators located.")
            return None

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")
        return None
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Error during browser cleanup: {e}")

# ------------------------------ SESSION MANAGEMENT (FOR API LOGIN FLOW) ------------------------------

_sessions: Dict[str, Dict[str, Any]] = {}
SESSION_TIMEOUT_MINUTES = 10

def _create_session(account_id: int, email: str, page: Page, context: BrowserContext, browser: Browser, is_main_page_2fa: bool) -> str:
    """Create a new login session and return session ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "account_id": account_id,
        "email": email,
        "page": page,
        "context": context,
        "browser": browser,
        "is_main_page_2fa": is_main_page_2fa,
        "created_at": datetime.now(timezone.utc)
    }
    logger.info(f"Created login session {session_id} for account {account_id}")
    return session_id

def _get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a login session by ID. Returns None if expired or not found."""
    session = _sessions.get(session_id)
    if not session:
        return None
    
    if datetime.now(timezone.utc) > session["created_at"] + timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        logger.warning(f"Login session {session_id} has expired")
        del _sessions[session_id]
        return None
    
    return session

async def _cleanup_and_remove_session(session_id: str):
    """Clean up browser resources and remove session from storage."""
    session = _sessions.get(session_id)
    if not session:
        return
    
    try:
        if session["browser"]:
            await session["browser"].close()
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")
    finally:
        del _sessions[session_id]
        logger.info(f"Removed login session {session_id}")

def _error_response(error: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {"success": False, "error": error}

def _success_response(requires_2fa: bool = False, message: str = "", session_id: str = None, email: str = None, account_id: int = None) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {"success": True, "requires_2fa": requires_2fa, "message": message}
    if session_id:
        response["session_id"] = session_id
    if email:
        response["email"] = email
    if account_id:
        response["account_id"] = account_id
    return response

# ------------------------------ API LOGIN FLOW (FOR FRONTEND) ------------------------------

async def start_turo_login(account_id: int, email: str, password: str) -> Dict[str, Any]:
    """
    Start Turo login process. Returns session_id if 2FA is needed, or completes login if no 2FA.
    Does NOT handle 2FA automatically - waits for frontend to provide code.
    """
    browser = None
    try:
        headless = settings.scraping.headless
        
        restored = await _try_restore_session(account_id, headless)
        if restored:
            page, context, browser = restored
            await browser.close()
            browser = None
            return _success_response(message="Login successful (session restored)")
        
        logger.info("Initiating Turo login automation...")
        page, context, browser = await launch_browser(headless=headless, storage_state_path=None)
        
        if not await _perform_credential_login(page, email, password):
            return _error_response("Failed to login with credentials")
        
        await page.wait_for_timeout(3000)
        
        if await check_for_success_element(page, [TEXT_CODE_BUTTON], iframe_content=None):
            success, is_main_page = await prepare_two_factor_auth(page)
            if not success:
                return _error_response("Failed to prepare 2FA page")
            
            await page.wait_for_timeout(2000)
            session_id = _create_session(account_id, email, page, context, browser, is_main_page)
            logger.info(f"2FA required - created session {session_id} (is_main_page={is_main_page})")
            browser = None
            return _success_response(requires_2fa=True, session_id=session_id, message="2FA code required")
        
        if await check_login_success(page):
            await save_storage_state(context, account_id=account_id, email=email)
            await browser.close()
            browser = None
            return _success_response(message="Login successful")
        
        return _error_response("Login failed - unable to confirm success")
    
    except Exception as e:
        logger.exception(f"Error in start_turo_login: {e}")
        return _error_response(str(e))
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser in start_turo_login: {e}")

async def submit_turo_2fa_code(session_id: str, code: str) -> Dict[str, Any]:
    """
    Submit 2FA code to complete login.
    """
    try:
        session = _get_session(session_id)
        if not session:
            return _error_response("Invalid or expired session")
        
        page = session["page"]
        is_main_page = session["is_main_page_2fa"]
        
        if not await submit_two_factor_auth(page, code, is_main_page):
            await _cleanup_and_remove_session(session_id)
            return _error_response("Failed to submit 2FA code")
        
        if await check_login_success(page):
            email = session["email"]
            account_id = session["account_id"]
            
            await save_storage_state(session["context"], account_id=account_id, email=email)
            await _cleanup_and_remove_session(session_id)
            return _success_response(message="Login successful", email=email, account_id=account_id)
        else:
            await _cleanup_and_remove_session(session_id)
            return _error_response("2FA code invalid or login failed")
    
    except Exception as e:
        logger.exception(f"Error in submit_turo_2fa: {e}")
        return _error_response(str(e))

# ------------------------------ END OF FILE ------------------------------