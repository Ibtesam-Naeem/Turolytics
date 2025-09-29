# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import async_playwright, Page, BrowserContext, Browser
from typing import Optional
from utils.logger import logger

# ------------------------------ CONFIGURATION ------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_VIEWPORT = {"width": 1366, "height": 768}
DEFAULT_TIMEOUT = 30000
DEFAULT_HEADLESS = False

BROWSER_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

ANTI_DETECTION_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
)

# ------------------------------ VALIDATION FUNCTIONS ------------------------------
def validate_viewport(viewport: dict[str, int]) -> bool:
    """Validate viewport dimensions."""
    return (isinstance(viewport, dict) and 
            all(k in viewport for k in ("width", "height")) and
            all(isinstance(viewport[k], int) and viewport[k] > 0 for k in ("width", "height")))

def validate_user_agent(user_agent: str) -> bool:
    """Validate user agent string."""
    return isinstance(user_agent, str) and bool(user_agent.strip())

# ------------------------------ BROWSER LAUNCH FUNCTION ------------------------------
async def launch_browser(
    headless: bool = DEFAULT_HEADLESS,
    user_agent: str = USER_AGENT,
    viewport: dict[str, int] = DEFAULT_VIEWPORT,
    timeout: int = DEFAULT_TIMEOUT,
    storage_state_path: Optional[str] = None,
) -> tuple[Page, BrowserContext, Browser]:
    """
    Launches a Chromium browser with standardized settings.
    
    Args:
        headless: Whether to run the browser in headless mode.
        user_agent: The user agent string to use for the browser context.
        viewport: The viewport size for the browser context.
        timeout: Timeout in milliseconds for page operations.
        storage_state_path: Optional path to storage state file for session restoration.
        
    Returns:
        A tuple containing (page, context, browser) objects.
        
    Raises:
        ValueError: If input parameters are invalid.
        Exception: If browser launch or context creation fails.
    """
    
    if not validate_user_agent(user_agent):
        raise ValueError("Invalid user agent string provided")
    
    if not validate_viewport(viewport):
        raise ValueError("Invalid viewport configuration provided")
    
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("Timeout must be a positive integer")
    
    browser = None
    playwright = None
    
    try:
        logger.info("Starting browser launch...")
        playwright = await async_playwright().start()
        
        logger.debug(f"Launching Chromium browser (headless: {headless})")
        browser = await playwright.chromium.launch(
            headless=headless,
            args=BROWSER_LAUNCH_ARGS,
        )
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            storage_state=storage_state_path,
        )
        
        page = await context.new_page()
        page.set_default_timeout(timeout)
        await page.add_init_script(ANTI_DETECTION_SCRIPT)
        
        logger.info("Browser launched successfully")
        return page, context, browser

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")

        if browser:
            try:
                await browser.close()
                logger.info("Browser closed successfully")
            except Exception:
                pass

        if playwright:
            try:
                await playwright.stop()
                logger.info("Playwright stopped successfully")
            except Exception:
                pass
        raise

# ------------------------------ END OF FILE ------------------------------