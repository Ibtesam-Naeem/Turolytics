# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
from typing import Optional
from core.utils.logger import logger

# ------------------------------ TEXT EXTRACTION HELPERS ------------------------------

async def safe_text(element, default: Optional[str] = None) -> Optional[str]:
    """Safely extract and strip text content from an element."""
    if not element:
        return default
    text = await element.text_content()
    return text.strip() if text else default

# ------------------------------ SCROLLING HELPERS ------------------------------

async def scroll_to_bottom_and_wait(page: Page, scroll_wait: int = 3000, final_wait: int = 2000) -> None:
    """Scroll to bottom of page and wait for content to load."""
    await page.wait_for_timeout(scroll_wait)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(final_wait)

# ------------------------------ END OF FILE ------------------------------
