# ------------------------------ IMPORTS ------------------------------
import getpass
from typing import Optional, Tuple

from playwright.async_api import Page, BrowserContext, Browser

from core.utils.logger import logger
from core.config.browser_settings import launch_browser
from core.security.session import verify_session_authenticated, save_storage_state, get_storage_state
from .helpers import get_iframe_content, search_for_error_messages, clear_form_inputs, check_for_success_element, click_continue_button_with_retry
from .selectors import (
    LOGIN_URL, CONTINUE_WITH_EMAIL_SELECTOR, EMAIL_SELECTOR, PASSWORD_SELECTOR,
    TEXT_CODE_BUTTON, CODE_INPUT_SELECTOR, FINAL_CONTINUE_BUTTON, CONTINUE_BUTTON_TEXT_SELECTOR,
    LOGIN_SUCCESS_URLS, LOGIN_SUCCESS_SELECTORS
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def get_credentials(email: str = None, password: str = None) -> Tuple[str, str]:
    """Get login credentials from user input if not provided."""
    if not email:
        try:
            email = input("Enter your Turo email: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Exception("Cannot read email from input. Please run the server in a terminal to enter credentials manually.")
    
    if not password:
        try:
            password = getpass.getpass("Enter your Turo password: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Exception("Cannot read password from input. Please run the server in a terminal to enter credentials manually.")
    
    if not email or not password:
        raise Exception("Turo credentials are required.")
    
    return email, password

async def get_2fa_code() -> str:
    """Get 2FA code from user input."""
    for attempt in range(3):
        try:
            code = input("Enter the 2FA code you received via text: ").strip()
            if code:
                return code
            logger.warning(f"2FA code cannot be empty. Please try again. (Attempt {attempt + 1}/3)")
        
        except (EOFError, KeyboardInterrupt):
            raise Exception("Cannot read 2FA code from input. Please run the server in a terminal to enter the code manually.")
    raise Exception("Failed to get valid 2FA code after 3 attempts")

async def check_login_success(page: Page) -> bool:
    """Check if login was successful by looking for success indicators."""
    for indicator in LOGIN_SUCCESS_URLS:
        try:
            await page.wait_for_url(indicator, timeout=5000)
            logger.info(f"Login successful! Redirected to: {indicator}")
            return True
        except:
            continue
    
    for selector in LOGIN_SUCCESS_SELECTORS:
        try:
            element = await page.wait_for_selector(selector, timeout=2000)
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
        await page.wait_for_timeout(1200)

        button = await page.wait_for_selector(CONTINUE_WITH_EMAIL_SELECTOR, timeout=10000)
        if not button:
            logger.error("'Continue with email' button not found.")
            return False

        await button.hover()
        await button.click()
        await page.wait_for_timeout(1000)
        logger.info("'Continue with email' clicked successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during open_turo_login: {e}")
        return False

async def login_with_credentials(page: Page, email: str = None, password: str = None) -> bool:
    """Login with credentials, fill form, and submit."""
    try:
        email, password = await get_credentials(email, password)
        
        for attempt in range(3):
            logger.info("Switching to login iframe...")
            iframe_content = await get_iframe_content(page)
            if not iframe_content:
                logger.error("Could not access iframe content.")
                return False

            logger.info("Filling in login credentials...")
            email_input = await iframe_content.wait_for_selector(EMAIL_SELECTOR, timeout=8000)
            password_input = await iframe_content.wait_for_selector(PASSWORD_SELECTOR, timeout=8000)

            await email_input.fill(email)
            await page.wait_for_timeout(300)
            await password_input.fill(password)
            await page.wait_for_timeout(800)

            await click_continue_button_with_retry(page, iframe_content, CONTINUE_BUTTON_TEXT_SELECTOR)
            await page.wait_for_timeout(2000)

            error_message = await search_for_error_messages(page, iframe_content)
            if error_message:
                logger.error(f"Login failed with error: '{error_message}'")
                await clear_form_inputs(page, [EMAIL_SELECTOR, PASSWORD_SELECTOR], iframe_content)
                if attempt < 2:
                    logger.warning(f"Retrying login (Attempt {attempt + 2}/3)...")
                continue

            if await check_for_success_element(page, [TEXT_CODE_BUTTON], iframe_content):
                logger.info("Login successful. Proceeding to 2FA.")
                return True
            
            logger.error("Login failed: No error message found and 2FA not triggered.")
            await clear_form_inputs(page, [EMAIL_SELECTOR, PASSWORD_SELECTOR], iframe_content)
            if attempt < 2:
                logger.warning(f"Retrying login (Attempt {attempt + 2}/3)...")

        logger.error("All login attempts failed.")
        return False

    except Exception as e:
        logger.exception(f"Error during login_with_credentials: {e}")
        return False

async def handle_two_factor_auth(page: Page) -> bool:
    """Handles the Turo two-factor authentication (2FA) step."""
    try:
        logger.info("Waiting for 2FA page...")

        try:
            text_button = await page.wait_for_selector(TEXT_CODE_BUTTON, timeout=5000)
            await text_button.click()
            logger.info("'Text code' button clicked on main page.")
            main_page_2fa = True
            iframe_content = None
        except:
            try:
                iframe_content = await get_iframe_content(page, timeout=10000)
                text_button = await iframe_content.wait_for_selector(TEXT_CODE_BUTTON, timeout=10000)
                await text_button.click()
                logger.info("'Text code' button clicked in iframe.")
                main_page_2fa = False

            except Exception as e:
                logger.error(f"Could not find 2FA text button: {e}")
                return False

        code = await get_2fa_code()

        if main_page_2fa:
            await page.fill(CODE_INPUT_SELECTOR, code)
            submit_btn = await page.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=10000)
        else:
            await iframe_content.fill(CODE_INPUT_SELECTOR, code)
            submit_btn = await iframe_content.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=10000)

        await submit_btn.click()
        await page.wait_for_timeout(2000)
        logger.info("2FA code submitted successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during handle_two_factor_auth: {e}")
        return False

async def complete_turo_login(headless: bool = True, account_id: int = 1, email: str = None, password: str = None) -> Optional[Tuple[Page, BrowserContext, Browser]]:
    """Log into Turo using manual email/password and 2FA input, or restore existing session."""
    try:
        if not email:
            email, _ = await get_credentials(email, password)
        
        storage_state = get_storage_state(account_id)
        if storage_state:
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
        
        logger.info("Initiating Turo login automation...")
        page, context, browser = await launch_browser(headless=headless, storage_state_path=None)
        
        logger.info("Proceeding with fresh login")
        
        if not await open_turo_login(page):
            return None

        for attempt in range(3):
            if await login_with_credentials(page, email, password):
                break
            logger.warning(f"Login attempt {attempt + 1} failed. Retrying...")
        else:
            logger.error("All login attempts failed.")
            return None

        if not await handle_two_factor_auth(page):
            return None

        logger.info("Checking if login was successful...")
        
        if await check_login_success(page):
            logger.info("Login successful, user has been successfully authenticated.")
            await save_storage_state(context, account_id=account_id)
            return page, context, browser
        else:
            logger.error("Unable to confirm a successful login - no success indicators located.")
            return None

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")
        try:
            if 'browser' in locals():
                await browser.close()
                logger.info("Browser closed successfully")

        except Exception as cleanup_error:
            logger.warning(f"Error during browser cleanup: {cleanup_error}")
        return None

# ------------------------------ END OF FILE ------------------------------