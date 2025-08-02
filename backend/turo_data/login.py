# ------------------------------ IMPORTS ------------------------------
import asyncio
import sys
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger

# ------------------------------ CONFIGURATION ------------------------------
load_dotenv()

LOGIN_URL = "https://turo.com/ca/en/login"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_VIEWPORT = {"width": 1366, "height": 768}

# Selectors
CONTINUE_BUTTON_SELECTOR = ".css-131npuy"
EMAIL_SELECTOR = 'input[type="email"][name="email"], #email'
PASSWORD_SELECTOR = 'input[type="password"][name="password"], #password'
TEXT_CODE_BUTTON = 'button.buttonSchumi--purple'
CODE_INPUT_SELECTOR = '#challengeCode'
FINAL_SUBMIT_BUTTON = 'button:has-text("Submit")'


# ------------------------------ BROWSER SETUP ------------------------------
async def launch_browser(headless=True):
    """
    Launches a Playwright Chromium browser instance with custom settings.

    args:
        headless: bool - Whether to run browser in headless mode.
    returns:
        page object
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport=DEFAULT_VIEWPORT,
    )
    page = await context.new_page()

    # Prevent detection as bot
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    return page


# ------------------------------ STEP 1: OPEN LOGIN PAGE ------------------------------
async def open_turo_login(page):
    """
    Navigates to Turo login page and clicks 'Continue with email'.

    args:
        page: Playwright page object
    returns:
        True if successful, False otherwise
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
async def login_with_credentials(page):
    """
    Prompts user for email & password, fills the login form, and submits.

    args:
        page: Playwright page object
    returns:
        True if login submitted successfully, False otherwise
    """
    try:
        email = input("Enter your Turo email: ").strip()
        password = input("Enter your Turo password: ").strip()

        if not email or not password:
            logger.error("Email and password cannot be empty.")
            return False

        logger.info("Switching to login iframe...")
        iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=8000)
        iframe_content = await iframe.content_frame()
        if not iframe_content:
            logger.error("Could not access iframe content.")
            return False

        logger.info("Filling in login credentials...")
        await (await iframe_content.wait_for_selector(EMAIL_SELECTOR, timeout=8000)).type(email, delay=100)
        await page.wait_for_timeout(300)
        await (await iframe_content.wait_for_selector(PASSWORD_SELECTOR, timeout=8000)).fill(password)
        await page.wait_for_timeout(800)

        # Click 'Continue' twice for reliability
        submit_btn = await iframe_content.wait_for_selector('button:has-text("Continue")', timeout=8000)
        await submit_btn.hover()

        box = await submit_btn.bounding_box()
        if box:
            await page.mouse.move(box["x"] + 5, box["y"] + 5)

        for _ in range(2):
            await submit_btn.click(force=True, delay=100)
            await page.wait_for_timeout(1200)

        logger.info("Credentials submitted successfully.")
        return True

    except Exception as e:
        logger.exception(f"Error during login_with_credentials: {e}")
        return False


# ------------------------------ STEP 3: HANDLE 2FA ------------------------------
async def handle_two_factor_auth(page):
    """
    Clicks 'Text code', waits for user to input received code, enters it, and clicks continue.
    """
    try:
        logger.info("Waiting for 2FA page...")
        await page.wait_for_selector(TEXT_CODE_BUTTON, timeout=10000)
        await page.click(TEXT_CODE_BUTTON)
        logger.info("'Text code' button clicked.")

        code = input("Enter the 2FA code you received via text: ").strip()
        if not code:
            logger.error("No code entered.")
            return False

        await page.fill(CODE_INPUT_SELECTOR, code)
        await page.wait_for_timeout(500)

        submit_btn = await page.wait_for_selector(FINAL_SUBMIT_BUTTON, timeout=10000)
        await submit_btn.click()
        await page.wait_for_timeout(1500)

        logger.info("2FA code submitted successfully.")
        await page.wait_for_timeout(15000)
        return True

    except Exception as e:
        logger.exception(f"Error during handle_two_factor_auth: {e}")
        return False


# ------------------------------ MAIN LOGIN FUNCTION ------------------------------
async def complete_turo_login(headless=False):
    """
    Automates the full Turo login process using manual input for credentials and 2FA.

    args:
        headless: bool - Whether to run browser in headless mode.
    returns:
        page object if login successful, None otherwise
    """
    try:
        logger.info("Starting Turo login automation...")

        page = await launch_browser(headless=headless)
        if not await open_turo_login(page):
            return None

        if not await login_with_credentials(page):
            return None

        if not await handle_two_factor_auth(page):
            return None

        logger.info("Waiting for dashboard page to load...")
        await page.wait_for_url("**/dashboard", timeout=30000)
        logger.info("Login successful, dashboard loaded.")

        return page

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")
        return None


# ------------------------------ TEST RUN ------------------------------
if __name__ == "__main__":
    async def main():
        page = await complete_turo_login(headless=False)
        if page:
            logger.info("Keeping browser open for inspection...")
            await asyncio.sleep(30)
        else:
            logger.error("Login process failed.")

    asyncio.run(main())
