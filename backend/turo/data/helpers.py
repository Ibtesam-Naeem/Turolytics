# ------------------------------ IMPORTS ------------------------------

import asyncio
import re
from collections import Counter
from typing import Optional, List, Any, Union, Dict, Callable, Awaitable
from playwright.async_api import Page, ElementHandle, Frame

from core.utils.browser_helpers import safe_text
from core.utils.logger import logger
from core.config.settings import TIMEOUT_IFRAME, TIMEOUT_SELECTOR_WAIT, DELAY_LONG, DELAY_SHORT

# ------------------------------ COMMON EXTRACTION HELPERS ------------------------------

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    match = re.search(pattern, text)
    return match.group(group) if match else None

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string like '$100.00' into a float."""
    if not amount_str:
        return None
    try:
        cleaned = amount_str.replace('$', '').replace(',', '')
        return float(cleaned)
        
    except (ValueError, TypeError):
        return None

async def try_selectors(
    element: Union[Page, ElementHandle], 
    selectors: List[str], 
    validator=None
) -> Optional[str]:
    """Try multiple selectors and return first valid result."""
    for selector in selectors:
        try:
            target = await element.query_selector(selector)
            text = await safe_text(target)
            if text and (not validator or validator(text)):
                return text.strip()
        except Exception:
            continue
    return None

async def get_text(element: Union[Page, ElementHandle], selector: str) -> Optional[str]:
    """Get text from an element using a selector."""
    target = await element.query_selector(selector)
    return await safe_text(target)

async def extract_texts_from_elements(
    element: Union[Page, ElementHandle], 
    selector: str,
    filter_func: Optional[Callable[[str], bool]] = None
) -> List[str]:
    """Extract text content from multiple elements matching a selector."""
    try:
        elements = await element.query_selector_all(selector)
        texts = []
        for el in elements:
            text = await safe_text(el)
            if text:
                if not filter_func or filter_func(text):
                    texts.append(text)
        return texts
    except Exception as e:
        logger.debug(f"Error extracting texts from elements: {e}")
        return []

# ------------------------------ NAVIGATION HELPERS ------------------------------

async def navigate_to_page(page: Page, url: str, page_name: str) -> bool:
    """Generic navigation function for Turo pages."""
    try:
        logger.info(f"Navigating to {page_name}...")
        await page.goto(url, wait_until="domcontentloaded")
        logger.info(f"Successfully navigated to {page_name}")
        return True
    except Exception as e:
        logger.exception(f"Error navigating to {page_name}: {e}")
        return False

async def navigate_and_extract(page: Page, url: str, page_name: str, extract_func: Callable[[Page], Awaitable[Any]]) -> Optional[Any]:
    """Navigate to page and extract data with error handling."""
    if not await navigate_to_page(page, url, page_name):
        logger.error(f"Failed to navigate to {page_name}")
        return None
    return await extract_func(page)

# ------------------------------ TURO LOGIN HELPERS ------------------------------

async def get_iframe_content(page: Page, timeout: int = TIMEOUT_IFRAME) -> Optional[Frame]:
    """Get the iframe content frame for Turo login forms."""
    try:
        iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=timeout)
        return await iframe.content_frame()
    except Exception as e:
        logger.debug(f"Error getting iframe content: {e}")
        return None

async def click_continue_button_with_retry(page: Page, iframe_content: Frame, continue_button_selector: str = "button:has-text('Continue')") -> bool:
    """Click the continue button with retry logic for iframe reloads."""
    try:
        submit_btn = await iframe_content.wait_for_selector(continue_button_selector, timeout=TIMEOUT_IFRAME)
        await submit_btn.click(force=True, delay=100)
        await page.wait_for_timeout(DELAY_LONG)
        return True
    except Exception as e:
        logger.debug("Retrying button click after iframe reload...")
        try:
            iframe = await page.wait_for_selector('iframe[data-testid="managedIframe"]', timeout=TIMEOUT_IFRAME)
            iframe_content = await iframe.content_frame()
            submit_btn = await iframe_content.wait_for_selector(continue_button_selector, timeout=TIMEOUT_IFRAME)
            await submit_btn.click(force=True, delay=100)
            await page.wait_for_timeout(DELAY_LONG)
            return True
            
        except Exception as retry_error:
            logger.error(f"Failed to click 'Continue' button: {retry_error}")
            return False

async def search_for_error_messages(page: Page, iframe_content: Optional[Frame] = None, error_messages: Optional[List[str]] = None) -> Optional[str]:
    """Search for specific error messages on the page and in iframe."""
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
    
    targets = [page]
    if iframe_content:
        targets.append(iframe_content)
    
    # First, try direct text matching
    for target in targets:
        for error_msg in error_messages:
            try:
                element = await target.query_selector(f'text="{error_msg}"')
                if element:
                    return error_msg
                    
                element = await target.query_selector(f'text*="{error_msg}"')
                if element:
                    return error_msg
            except Exception:
                continue
    
    # Then, search through error selector elements
    for target in targets:
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

async def clear_form_inputs(page: Page, input_selectors: List[str], iframe_content: Optional[Frame] = None) -> None:
    """Clear form input fields on form submission failure."""
    targets = [page]
    if iframe_content:
        targets.append(iframe_content)
    
    for target in targets:
        try:
            for selector in input_selectors:
                input_element = await target.query_selector(selector)
                if input_element:
                    await input_element.fill('')
            await page.wait_for_timeout(DELAY_SHORT)
        except Exception:
            pass

async def check_for_success_element(page: Page, success_selectors: List[str], iframe_content: Optional[Frame] = None) -> bool:
    """Check if success indicators are found, indicating successful form submission."""
    targets = [page]
    if iframe_content:
        targets.append(iframe_content)
    
    for target in targets:
        for selector in success_selectors:
            try:
                if await target.query_selector(selector):
                    return True
            except Exception:
                continue
    return False

# ------------------------------ SCRAPING DECORATORS ------------------------------

def scraping_function(page_name: str):
    """Decorator for scraping functions that adds logging and error handling."""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"Starting to scrape {page_name}...")
                result = await func(*args, **kwargs)
                logger.info(f"{page_name} scraping completed successfully!")
                return result
            except Exception as e:
                logger.exception(f"Error scraping {page_name}: {e}")
                return None
        return wrapper
    return decorator

# ------------------------------ PARALLEL PROCESSING HELPERS ------------------------------

def count_statuses(items: List[Any], status_key: str = 'status') -> Dict[str, int]:
    """Count status occurrences in a list of items.
    
    Args:
        items: List of dictionaries/objects with status information
        status_key: Key to access status in each item (default: 'status')
        
    Returns:
        Dictionary mapping status values to counts
    """
    status_counts = Counter(item.get(status_key) for item in items if item.get(status_key))
    return dict(status_counts)

async def process_items_in_parallel(
    items: List[Any],
    extract_func: Callable[[Any, int], Awaitable[Any]],
    item_type: str = "item",
    parallel_threshold: int = 5
) -> List[Any]:
    """Process multiple items (e.g., cards, elements) in parallel or sequentially."""
    if not items:
        return []
    
    async def extract_with_error_handling(item: Any, index: int):
        """Extract data with error handling."""
        try:
            return await extract_func(item, index)
        except Exception as e:
            logger.debug(f"Error processing {item_type} {index}: {e}")
            return None
    
    if len(items) <= parallel_threshold:
        results = []
        for i, item in enumerate(items):
            result = await extract_with_error_handling(item, i)
            results.append(result)
    else:
        tasks = [extract_with_error_handling(item, i) for i, item in enumerate(items)]
        results = await asyncio.gather(*tasks)
    
    return [result for result in results if result is not None]

# ------------------------------ END OF FILE ------------------------------
