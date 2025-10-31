# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
from typing import Optional, Callable, Awaitable
from functools import wraps
from core.utils.logger import logger

# ------------------------------ BROWSER HELPER FUNCTIONS ------------------------------
async def retry_operation(func: Callable[..., Awaitable[bool]], attempts: int = 3, *args, **kwargs) -> bool:
    """Retry an operation with specified number of attempts."""
    for attempt in range(attempts):
        if await func(*args, **kwargs):
            return True
        logger.debug(f"Attempt {attempt+1}/{attempts} failed.")
    return False

async def close_browser_safely(browser) -> None:
    """Safely close browser with error handling."""
    try:
        if browser:
            await browser.close()
            
    except Exception as e:
        logger.warning(f"Error during browser cleanup: {e}")

# ------------------------------ TEXT EXTRACTION HELPERS ------------------------------
async def safe_text(element, default: Optional[str] = None) -> Optional[str]:
    """Safely extract and strip text content from an element."""
    if not element:
        return default
    text = await element.text_content()
    return text.strip() if text else default

# ------------------------------ DECORATORS ------------------------------
def safe_scrape(default_return):
    """Decorator for safe scraping functions with consistent error handling."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                logger.debug(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper
    return decorator

async def scroll_to_bottom_and_wait(page: Page, scroll_wait: int = 3000, final_wait: int = 2000) -> None:
    """Scroll to bottom of page and wait for content to load."""
    await page.wait_for_timeout(scroll_wait)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(final_wait)

# ------------------------------ END OF FILE ------------------------------