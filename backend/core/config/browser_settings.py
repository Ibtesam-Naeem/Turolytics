# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import async_playwright, Page, BrowserContext, Browser
from typing import Optional
import logging

from core.config.settings import settings

logger = logging.getLogger(__name__)

# ------------------------------ USER AGENT ------------------------------
USER_AGENT = settings.scraping.user_agent

DEFAULT_VIEWPORT = {"width": 1366, "height": 768}
DEFAULT_TIMEOUT = 30000

BROWSER_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

ANTI_DETECTION_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
)

# ------------------------------ BROWSER LAUNCH FUNCTION ------------------------------
async def launch_browser(
    headless: bool = None,
    user_agent: str = USER_AGENT,
    viewport: dict = DEFAULT_VIEWPORT,
    timeout: int = DEFAULT_TIMEOUT,
    storage_state_path: Optional[str] = None,
) -> tuple[Page, BrowserContext, Browser]:
    """Launches a Chromium browser with standardized settings."""
    
    if headless is None:
        headless = settings.scraping.headless
    
    playwright = None
    browser = None
    
    try:
        playwright = await async_playwright().start()
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
        
        return page, context, browser

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
        raise

# ------------------------------ END OF FILE ------------------------------
