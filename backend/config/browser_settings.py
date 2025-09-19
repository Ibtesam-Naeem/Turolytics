# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page, BrowserContext, Browser, async_playwright
from typing import Optional
from utils.logger import logger

# ------------------------------ CONFIGURATION ------------------------------
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_VIEWPORT: dict[str, int] = {"width": 1366, "height": 768}

BROWSER_LAUNCH_ARGS: list[str] = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

# ------------------------------ CONSTANTS ------------------------------
DEFAULT_TIMEOUT: int = 30000  
DEFAULT_HEADLESS: bool = True
ANTI_DETECTION_SCRIPT: str = (
    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
)

# ------------------------------ VALIDATION FUNCTIONS ------------------------------
def validate_viewport(viewport: dict[str, int]):
    """
    Validate viewport dimensions.
    
    Args:
        viewport: Dictionary containing width and height.
        
    Returns:
        bool: True if viewport is valid, False otherwise.
    """
    if not isinstance(viewport, dict):
        return False
    
    required_keys = {"width", "height"}
    if not all(key in viewport for key in required_keys):
        return False
    
    if not all(isinstance(viewport[key], int) and viewport[key] > 0 for key in required_keys):
        return False
    
    return True

def validate_user_agent(user_agent: str) -> bool:
    """
    Validate user agent string.
    
    Args:
        user_agent: User agent string to validate.
        
    Returns:
        bool: True if user agent is valid, False otherwise.
    """
    return isinstance(user_agent, str) and len(user_agent.strip()) > 0

# ------------------------------ BROWSER LAUNCH FUNCTION ------------------------------
async def launch_browser(
    headless: bool = DEFAULT_HEADLESS,
    user_agent: str = USER_AGENT,
    viewport: dict[str, int] = DEFAULT_VIEWPORT,
    timeout: int = DEFAULT_TIMEOUT,
    storage_state_path: Optional[str] = None,   
):
    """
    Launch a Chromium browser with standardized settings.

    Args:
        headless: Whether to run the browser in headless mode.
        user_agent: The user agent string to use for the browser context.
        viewport: The viewport size for the browser context.
        timeout: Timeout in milliseconds for page operations.

    Returns:
        A tuple containing (page, context, browser) objects.
        The caller is responsible for closing these resources.

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
    
    try:
        logger.info("Starting Playwright...")
        playwright = await async_playwright().start()
        
        logger.info("Launching Chromium browser")
        browser = await playwright.chromium.launch(
            headless=headless,
            args=BROWSER_LAUNCH_ARGS,
        )
        
        logger.debug("Creating browser context")
        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            storage_state=storage_state_path if storage_state_path else None,
        )
        
        logger.debug("Creating new page")
        page = await context.new_page()
        
        page.set_default_timeout(timeout)
        
        logger.debug("Adding anti-detection script")
        await page.add_init_script(ANTI_DETECTION_SCRIPT)
        
        logger.info("Browser launched successfully")
        return page, context, browser
        
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")

        try:
            if 'browser' in locals():
                await browser.close()
            if 'playwright' in locals():
                await playwright.stop()
                
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")
        raise

# ------------------------------ EXPORTS ------------------------------
__all__ = [
    "launch_browser",
    "USER_AGENT",
    "DEFAULT_VIEWPORT",
    "BROWSER_LAUNCH_ARGS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_HEADLESS",
    "validate_viewport",
    "validate_user_agent",
]


