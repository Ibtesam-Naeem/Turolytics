# ---------------- IMPORTS ----------------
import asyncio
import sys
import os
from typing import Optional
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- CONSTANTS ----------------
LOGIN_URL = "https://turo.com/ca/en/login"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_VIEWPORT = {"width": 1366, "height": 768}
CONTINUE_BUTTON_SELECTOR = ".css-131npuy"

EMAIL_SELECTOR = 'input[type="email"][name="email"], #email'
PASSWORD_SELECTOR = 'input[type="password"][name="password"], #password'
SUBMIT_BUTTON_SELECTOR = 'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")'


# ---------------- STEP 1: CLICK "CONTINUE WITH EMAIL" ----------------
async def initiate_turo_login(headless: bool = True) -> Optional[Page]:
    """
    Launches browser and clicks 'Continue with email' on Turo login page.
    """
    try:
        logger.info("Launching Playwright session...")
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

        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        logger.info("Navigating to Turo login page...")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        button = await page.wait_for_selector(CONTINUE_BUTTON_SELECTOR, timeout=10000)
        if not button:
            logger.error("Continue with email button not found.")
            return None

        text = await button.text_content()
        if "Continue with email" not in text:
            logger.error(f"Unexpected button text: '{text}'")
            return None

        await button.hover()
        await page.wait_for_timeout(300)
        await button.click()
        await page.wait_for_timeout(1000)

        logger.info("Continue with email clicked successfully.")
        return page

    except Exception as e:
        logger.exception(f"Error during initiate_turo_login: {e}")
        return None


# ---------------- STEP 2: ENTER EMAIL + PASSWORD ----------------
async def login_with_credentials(page: Page) -> bool:
    """
    Enters email/password and submits the login form.
    """
    try:
        email = os.getenv("TURO_EMAIL")
        password = os.getenv("TURO_PASSWORD")

        if not email or not password:
            logger.error("TURO_EMAIL and TURO_PASSWORD must be set in .env or in the environment variables")
            return False

        logger.info("Filling in login credentials...")

        logger.info("Switching to login iframe...")
        iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=8000)
        iframe_content = await iframe.content_frame()
        
        if not iframe_content:
            logger.error("Could not access iframe content")
            return False

        # Now work within the iframe context
        email_field = await iframe_content.wait_for_selector(EMAIL_SELECTOR, timeout=8000)
        await email_field.type(email, delay=100)  # mimics real typing
        await page.wait_for_timeout(300)

        password_field = await iframe_content.wait_for_selector(PASSWORD_SELECTOR, timeout=8000)
        await password_field.fill(password)
        await page.wait_for_timeout(800)

        # Look for the Continue button within the iframe
        submit_button = await iframe_content.wait_for_selector('button:has-text("Continue")', timeout=8000)
        await submit_button.hover()
        await page.wait_for_timeout(300)

        # Move mouse near the button to simulate interaction
        box = await submit_button.bounding_box()
        if box:
            await page.mouse.move(box["x"] + 5, box["y"] + 5)
            await page.wait_for_timeout(200)

        # First click
        await submit_button.click(force=True, delay=100)
        await page.wait_for_timeout(1500)

        # Second click (in case the first didn't register properly)
        await submit_button.click(force=True, delay=100)
        await page.wait_for_timeout(3000)


        # Check for error messages first
        try:
            error_elements = await iframe_content.locator('text=required, text=invalid, text=error, text=failed').count()
            if error_elements > 0:
                logger.warning("Login form shows errors - please check manually")
                logger.info("Waiting 30 seconds for manual intervention...")
                await page.wait_for_timeout(30000)
        except:
            pass

        # Wait longer for the page to process
        await page.wait_for_timeout(5000)

        # Check current URL
        current_url = page.url
        logger.info(f"Current URL: {current_url}")

        # Try multiple success checks
        try:
            await page.wait_for_url("**/host/**", timeout=10000)
            logger.info("Login successful. Host dashboard loaded.")
            return True
        
        except:
            host_elements = await page.locator('a[href*="/host/"], [data-testid*="host"]').count()
            if host_elements > 0:
                logger.info("Login successful. Host elements detected.")
                return True

            if "login" in current_url.lower():
                logger.warning("Still on login page - may need manual verification")
                logger.info("Please complete any verification steps manually")
                logger.info("Waiting 60 seconds for manual completion...")
                await page.wait_for_timeout(60000)
                
                try:
                    await page.wait_for_url("**/host/**", timeout=10000)
                    logger.info("Login successful after manual verification.")
                    return True
                except:
                    final_host_elements = await page.locator('a[href*="/host/"], [data-testid*="host"]').count()
                    if final_host_elements > 0:
                        logger.info("Login successful after manual verification.")
                        return True

        logger.warning("Login status unclear - please check manually")
        return False

    except Exception as e:
        logger.exception(f"Error during login_with_credentials: {e}")
        return False

# ---------------- COMBINED LOGIN FUNCTION ----------------
async def complete_turo_login(headless: bool = False) -> Optional[Page]:
    """
    Automates full Turo login using email/password flow.
    """
    try:
        logger.info("Starting full Turo login process...")

        page = await initiate_turo_login(headless=headless)
        if not page:
            logger.error("Failed at initiate_turo_login.")
            return None

        success = await login_with_credentials(page)
        if success:
            logger.info("Full login process completed successfully.")
            return page

        logger.error("Failed at login_with_credentials.")
        return None

    except Exception as e:
        logger.exception(f"Error in complete_turo_login: {e}")
        return None


# ---------------- TEST RUN ----------------
if __name__ == "__main__":
    async def main():
        page = await complete_turo_login(headless=False)
        if page:
            logger.info("Login succeeded. Keeping browser open for inspection...")
            await asyncio.sleep(30)
        else:
            logger.error("Login process failed.")

    asyncio.run(main())
