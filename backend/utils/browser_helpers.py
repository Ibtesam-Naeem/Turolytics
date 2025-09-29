# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page, Frame
from typing import Optional, Callable, Awaitable
from functools import wraps
import re
from utils.logger import logger

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

async def get_iframe_content(page, timeout: int = 8000):
    """
    Get the iframe content frame for login forms.

    Args:
        page: Playwright page object.
        timeout: Timeout in milliseconds for iframe selector.

    Returns:
        Frame: The iframe content frame.
    """
    iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=timeout)
    return await iframe.content_frame()

async def click_continue_button_with_retry(page: Page, iframe_content, continue_button_selector: str = "button:has-text('Continue')") -> bool:
    """Click the continue button with retry logic for iframe reloads."""
    try:
        submit_btn = await iframe_content.wait_for_selector(continue_button_selector, timeout=8000)
        await submit_btn.click(force=True, delay=100)
        await page.wait_for_timeout(1500)
        return True

    except Exception as e:
        logger.debug("Retrying button click after iframe reload...")

        try:
            iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=8000)
            iframe_content = await iframe.content_frame()
            submit_btn = await iframe_content.wait_for_selector(continue_button_selector, timeout=8000)
            await submit_btn.click(force=True, delay=100)
            await page.wait_for_timeout(1500)
            return True
            
        except Exception as retry_error:
            logger.error(f"Failed to click 'Continue' button: {retry_error}")
            return False

# ------------------------------ TEXT EXTRACTION HELPERS ------------------------------
async def safe_text(element, default: Optional[str] = None) -> Optional[str]:
    """Safely extract and strip text content from an element."""
    if not element:
        return default
    text = await element.text_content()
    return text.strip() if text else default

def normalize_currency(amount_str: str) -> float:
    """Normalize currency string to float value."""
    if not amount_str:
        return 0.0
    
    cleaned = re.sub(r"[^\d.]", "", amount_str)
    
    try:
        return float(cleaned)

    except ValueError:
        return 0.0

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

# ------------------------------ ERROR DETECTION HELPER FUNCTIONS ------------------------------
async def search_for_error_messages(page: Page, iframe_content=None, error_messages=None):
    """
    Search for specific error messages on the page and in iframe.
    
    Args:
        page: Playwright page object
        iframe_content: Iframe content frame if available
        error_messages: List of error messages to search for. If None, uses default common errors.
        
    Returns:
        str | None: Error message if found, None otherwise
    """
    if error_messages is None:
        error_messages = [
            'Please enter a valid email',
            'Password is required',
            'Please check your email and password.'
        ]
    
    error_selectors = [
        'div[role="alert"]',
        '.error-message',
        '.error',
        '[data-testid="error"]',
        '.alert-error',
        '.form-error',
        '.validation-error',
        '.alert',
        '.notification',
        '[class*="error"]',
        '[class*="alert"]'
    ]
    
    for error_msg in error_messages:
        try:
            element = await page.query_selector(f'text="{error_msg}"')
            if element:
                return error_msg
                
            element = await page.query_selector(f'text*="{error_msg}"')

            if element:
                return error_msg
                
        except Exception:
            continue
    
    if iframe_content:
        for error_msg in error_messages:
            try:
                element = await iframe_content.query_selector(f'text="{error_msg}"')
                if element:
                    return error_msg
                    
                element = await iframe_content.query_selector(f'text*="{error_msg}"')
                if element:
                    return error_msg
                
            except Exception:
                continue
    
    search_targets = [page]
    if iframe_content:
        search_targets.append(iframe_content)
    
    for target in search_targets:
        for selector in error_selectors:
            try:
                error_elements = await target.query_selector_all(selector)
                for element in error_elements:
                    try:
                        error_text = await element.text_content()
                        if error_text:
                            error_text = error_text.strip()
                            for target_error in error_messages:
                                if target_error.lower() in error_text.lower():
                                    return target_error
                                
                    except Exception:
                        continue

            except Exception:
                continue
    
    return None

async def clear_form_inputs(page: Page, input_selectors: list, iframe_content=None):
    """
    Clear form input fields on form submission failure.
    
    Args:
        page: Playwright page object
        input_selectors: List of CSS selectors for input fields to clear
        iframe_content: Iframe content frame if available
    """
    try:
        if iframe_content:
            try:
                for selector in input_selectors:
                    input_element = await iframe_content.query_selector(selector)
                    if input_element:
                        await input_element.fill('')
                await page.wait_for_timeout(500)
            except Exception as e:
                pass
        
        try:
            for selector in input_selectors:
                input_element = await page.query_selector(selector)
                if input_element:
                    await input_element.fill('')
            await page.wait_for_timeout(500)

        except Exception as e:
            pass
            
    except Exception as e:
        pass

async def check_for_success_element(page: Page, success_selectors: list, iframe_content=None):
    """
    Check if success indicators are found, indicating successful form submission.
    
    Args:
        page: Playwright page object
        success_selectors: List of CSS selectors for success indicators
        iframe_content: Iframe content frame if available
        
    Returns:
        bool: True if success element found, False otherwise
    """
    try:
        for selector in success_selectors:
            element = await page.query_selector(selector)
            if element:
                return True
        
        if iframe_content:
            for selector in success_selectors:
                element = await iframe_content.query_selector(selector)
                if element:
                    return True
        
        return False
        
    except Exception as e:
        return False

async def scroll_to_bottom_and_wait(page: Page, scroll_wait: int = 3000, final_wait: int = 2000) -> None:
    """Scroll to bottom of page and wait for content to load."""
    await page.wait_for_timeout(scroll_wait)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(final_wait)
