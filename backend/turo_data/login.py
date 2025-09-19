# ------------------------------ IMPORTS ------------------------------
import getpass
import os

from playwright.async_api import Page

from utils.logger import logger
from utils.browser_helpers import get_iframe_content, search_for_error_messages, clear_form_inputs, check_for_success_element
from config import launch_browser
from utils.session import get_storage_state_path, verify_session_authenticated, save_storage_state

# ------------------------------ SELECTORS ------------------------------
LOGIN_URL = "https://turo.com/ca/en/login"
CONTINUE_BUTTON_SELECTOR = ".css-131npuy"
EMAIL_SELECTOR = 'input[type="email"][name="email"], #email'
PASSWORD_SELECTOR = 'input[type="password"][name="password"], #password'
TEXT_CODE_BUTTON = 'button.buttonSchumi--purple'
CODE_INPUT_SELECTOR = '#challengeCode'
FINAL_CONTINUE_BUTTON = 'button:has-text("Submit")'

# ------------------------------ HELPER FUNCTIONS ------------------------------
async def click_continue_button_with_retry(page: Page, iframe_content):
    """
    Click the continue button with retry logic for iframe reloads.

    Args:
        page: Playwright page object.
        iframe_content: The iframe content frame.

    Returns:
        None
    """
    try:
        submit_btn = await iframe_content.wait_for_selector('button:has-text("Continue")', timeout=8000)
        await submit_btn.click(force=True, delay=100)
        await page.wait_for_timeout(1500)

    except Exception:
        logger.warning("Retrying button click after iframe reload...")
        iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=8000)
        iframe_content = await iframe.content_frame()
        submit_btn = await iframe_content.wait_for_selector('button:has-text("Continue")', timeout=8000)
        await submit_btn.click(force=True, delay=100)
        await page.wait_for_timeout(1500)

# ------------------------------ STEP 1: OPEN LOGIN PAGE ------------------------------
async def open_turo_login(page: Page):
    """
    Navigates to Turo login page and clicks 'Continue with email' button 
    if user signs in with email.

    Args:
        page: Playwright page object.

    Returns:
        bool: True if successful, Otherwise False.
    """
    try:
        logger.info("Navigating to Turo login page...")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1200)

        button = await page.wait_for_selector(CONTINUE_BUTTON_SELECTOR, timeout=10000)
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

# ------------------------------ STEP 2: SUBMIT CREDENTIALS ------------------------------
async def login_with_credentials(page: Page):
    """
    Securely prompts user for email & password, fills the login form, and submits.
    Uses input() for email and getpass.getpass() for secure password input.
    Validates that 2FA prompt appears before proceeding.
    Clears input fields on failure to ensure no stale credentials are used.
    Searches for specific error messages and handles them appropriately.

    Args:
        page: The active browser page.

    Returns:
        bool: True if login submitted and 2FA triggered successfully, Otherwise False.
    """
    try:
        for attempt in range(3):
            email = input("Enter your Turo email: ").strip()
            password = getpass.getpass("Enter your Turo password: ").strip()

            if not email or not password:
                logger.warning("Email and password cannot be empty. Please try again.")
                continue

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

            await click_continue_button_with_retry(page, iframe_content)

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

# ------------------------------ STEP 3: HANDLE 2FA ------------------------------
async def handle_two_factor_auth(page: Page):
    """
    Handles the Turo two-factor authentication (2FA) step.

    Args:
        page: Playwright page object.

    Returns:
        bool: True if 2FA is successfully completed, Otherwise False.
    """
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

        for attempt in range(3):
            code = input("Enter the 2FA code you received via text: ").strip()
            if code:
                break
            logger.warning(f"2FA code cannot be empty. Please try again. (Attempt {attempt + 1}/3)")
        else:
            return False

        if main_page_2fa:
            await page.fill(CODE_INPUT_SELECTOR, code)
            await page.wait_for_timeout(500)
            submit_btn = await page.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=10000)
        else:
            await iframe_content.fill(CODE_INPUT_SELECTOR, code)
            await page.wait_for_timeout(500)
            submit_btn = await iframe_content.wait_for_selector(FINAL_CONTINUE_BUTTON, timeout=10000)

        await submit_btn.click()
        await page.wait_for_timeout(2000)

        logger.info("2FA code submitted successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during handle_two_factor_auth: {e}")
        return False

# ------------------------------ MAIN LOGIN FUNCTION ------------------------------
async def complete_turo_login(headless: bool = False):
    """
    Logs into Turo using manual email/password and 2FA input.

    Args:
        headless (bool): Run browser in headless mode. # For testing purposes

    Returns:
        tuple | None: (page, context, browser) if login succeeds, Otherwise None.
    """
    try:
        logger.info("Initiating Turo login automation...")

        storage_path = get_storage_state_path()

        page, context, browser = await launch_browser(
            headless=headless,
            storage_state_path=storage_path if os.path.exists(storage_path) else None,
        )

        if os.path.exists(storage_path):
            logger.info("Attempting session restore via storage state...")
            if await verify_session_authenticated(page):
                logger.info("Session restored successfully - no login required!")
                return page, context, browser
            else:
                logger.info("Stored session invalid or expired. Proceeding with interactive login.")
        if not await open_turo_login(page):
            return None

        for attempt in range(3):
            if await login_with_credentials(page):
                break
            logger.warning(f"Login attempt {attempt + 1} failed. Retrying...")
        else:
            logger.error("All login attempts failed.")
            return None

        if not await handle_two_factor_auth(page):
            return None

        logger.info("Checking if login was successful...")
        
        success_indicators = [
            "**/dashboard",
            "**/trips",
            "**/trips/booked",
            "**/trips/booked?recentUpdates=true",
            "**/account",
            "**/profile"
        ]
        
        success_detected = False
        for indicator in success_indicators:
            try:
                await page.wait_for_url(indicator, timeout=5000)
                logger.info(f"Login successful! Redirected to: {indicator}")
                success_detected = True
                break

            except:
                continue
        
        if not success_detected:
            try:
                await page.wait_for_timeout(3000)
                
                success_selectors = [
                    '[data-testid="user-menu"]',
                    '.user-menu',
                    '.account-menu',
                    '[aria-label*="Account"]',
                    '[aria-label*="Profile"]',
                    '.avatar',
                    '.user-avatar'
                ]
                
                for selector in success_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            logger.info(f"Login successful - Found success indicator: {selector}")
                            success_detected = True
                            break

                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not check for success elements: {e}")
        
        if success_detected:
            logger.info("Login successful, user has been successfully authenticated.")
            await save_storage_state(context)
            return page, context, browser
        else:
            logger.error("Unable to confirm a successful login - no success indicators located.")
            return None

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")

        try:
            if 'browser' in locals():
                await browser.close()
        except Exception as cleanup_error:
            logger.warning(f"Error during browser cleanup: {cleanup_error}")
        return None

# ------------------------------ END OF FILE ------------------------------