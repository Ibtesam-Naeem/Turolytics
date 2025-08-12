# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page

from dotenv import load_dotenv

from utils.logger import logger
from utils.browser_helpers import get_iframe_content
from config import launch_browser

# ------------------------------ CONFIGURATION ------------------------------
load_dotenv()

LOGIN_URL = "https://turo.com/ca/en/login"

# ------------------------------ SELECTORS ------------------------------
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
    Prompts user for email & password, fills the login form, and submits.
    Validates that 2FA prompt appears before proceeding.
    Clears input fields on failure to ensure no stale credentials are used.

    Args:
        page: The active browser page.

    Returns:
        bool: True if login submitted and 2FA triggered successfully, Otherwise False.
    """
    try:
        for attempt in range(3):
            email = input("Enter your Turo email: ").strip()
            password = input("Enter your Turo password: ").strip()

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

            try:
                await iframe_content.wait_for_selector(TEXT_CODE_BUTTON, timeout=8000)
                logger.info("Login successful. Proceeding to 2FA.")
                return True
            
            except:
                try:
                    await page.wait_for_timeout(2000)  # Wait for page transition
                    text_button = await page.wait_for_selector(TEXT_CODE_BUTTON, timeout=5000)
                    if text_button:
                        logger.info("Login successful. Found 2FA button on main page.")
                        return True
                except:
                    pass
                
                try:
                    email_input = await iframe_content.query_selector(EMAIL_SELECTOR)
                    password_input = await iframe_content.query_selector(PASSWORD_SELECTOR)
                    if email_input and password_input:
                        await email_input.fill('')
                        await password_input.fill('')
                        await page.wait_for_timeout(500)

                except Exception:
                    logger.warning("Could not clear inputs — elements may have been detached.")

                try:
                    error_selector = 'div[role="alert"], .error-message'
                    error_elem = await iframe_content.query_selector(error_selector)
                    if error_elem:
                        error_text = await error_elem.text_content()
                        logger.error(f"Login failed: {error_text.strip()}")
                    else:
                        logger.error("Login failed: 2FA not triggered and no error message found.")

                except Exception:
                    logger.error("Login failed: Could not check for error messages (iframe detached).")
                
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
    Automates the full Turo login process using manual input for credentials and 2FA.

    Args:
        headless: Whether to run browser in headless mode.

    Returns:
        tuple[Page, Any, Any] | None: Tuple of (page, context, browser) if login successful, otherwise None.
    """
    try:
        logger.info("Starting Turo login automation...")

        page, context, browser = await launch_browser(headless=headless)
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

        logger.info("Waiting for dashboard page to load...")
        await page.wait_for_url("**/dashboard", timeout=30000)
        logger.info("Login successful, dashboard loaded.")

        return page, context, browser

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")

        try:
            if 'browser' in locals():
                await browser.close()
        except Exception as cleanup_error:
            logger.warning(f"Error during browser cleanup: {cleanup_error}")
        return None

# ------------------------------ END OF FILE ------------------------------
