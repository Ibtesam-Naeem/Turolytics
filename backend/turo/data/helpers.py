# ------------------------------ IMPORTS ------------------------------

import asyncio
import re
from collections import Counter
from typing import Optional, List, Any, Union, Dict, Callable, Awaitable
from playwright.async_api import Page, ElementHandle, Frame
import logging

from core.config.settings import TIMEOUT_IFRAME, TIMEOUT_SELECTOR_WAIT, DELAY_LONG, DELAY_SHORT, DELAY_MEDIUM

logger = logging.getLogger(__name__)

# ------------------------------ COMMON EXTRACTION HELPERS ------------------------------

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    match = re.search(pattern, text)
    return match.group(group) if match else None

async def try_selectors(
    element: Union[Page, ElementHandle], 
    selectors: List[str], 
    validator=None
) -> Optional[str]:
    """Try multiple selectors and return first valid result."""
    for selector in selectors:
        try:
            target = await element.query_selector(selector)
            text = (await target.text_content() or '').strip() if target else None
            if text and (not validator or validator(text)):
                return text.strip()
        except Exception:
            continue
    return None

async def get_text(element: Union[Page, ElementHandle], selector: str) -> Optional[str]:
    """Get text from an element using a selector."""
    target = await element.query_selector(selector)
    return (await target.text_content() or '').strip() if target else None

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
            text = (await el.text_content() or '').strip() if el else None
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

# ------------------------------ EARNINGS YEAR SELECTION HELPERS ------------------------------

async def select_earnings_year(page: Page, year: str) -> bool:
    """Select a year from the earnings page dropdown.
    
    Args:
        page: Playwright page object
        year: Year to select (e.g., "2025", "2026")
    
    Returns:
        True if year was successfully selected, False otherwise
    """
    try:
        from .selectors import (
            EARNINGS_YEAR_DROPDOWN_BUTTON,
            EARNINGS_YEAR_DROPDOWN_ITEM,
            EARNINGS_YEAR_DROPDOWN_LABEL
        )
        
        logger.info(f"Selecting year {year} from earnings dropdown...")
        
        # Click the dropdown button to open the menu
        dropdown_button = await page.wait_for_selector(
            EARNINGS_YEAR_DROPDOWN_BUTTON,
            timeout=TIMEOUT_SELECTOR_WAIT
        )
        if not dropdown_button:
            logger.error(f"Could not find year dropdown button")
            return False
        
        # Ensure button is in view and ready
        await dropdown_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(DELAY_SHORT)
        
        # Verify button is actually visible and clickable
        is_visible = await dropdown_button.is_visible()
        if not is_visible:
            logger.error("Dropdown button is not visible")
            return False
        
        logger.debug("Clicking dropdown button...")
        await dropdown_button.click(force=True)
        await page.wait_for_timeout(DELAY_MEDIUM)
        
        # Wait for dropdown items to appear (more reliable than waiting for menu container)
        # Try multiple approaches to find the dropdown items
        year_items = []
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                # Try to find dropdown items directly - wait for at least one to be visible
                try:
                    # Wait for first item to be visible (Playwright waits for visible by default)
                    await page.wait_for_selector(
                        EARNINGS_YEAR_DROPDOWN_ITEM,
                        timeout=2000
                    )
                except:
                    # If that fails, just query for items anyway
                    pass
                
                year_items = await page.query_selector_all(EARNINGS_YEAR_DROPDOWN_ITEM)
                # Filter to only visible items
                visible_items = []
                for item in year_items:
                    try:
                        if await item.is_visible():
                            visible_items.append(item)
                    except:
                        pass
                
                if visible_items:
                    year_items = visible_items
                    logger.debug(f"Found {len(year_items)} visible dropdown items on attempt {attempt + 1}")
                    break
                elif year_items:
                    # If we found items but they're not visible, still use them (might be in a portal/overlay)
                    logger.debug(f"Found {len(year_items)} dropdown items (may not be visible) on attempt {attempt + 1}")
                    break
                
                # If no items found, wait a bit and try again
                if attempt < max_retries - 1:
                    await page.wait_for_timeout(DELAY_MEDIUM)
            except Exception as e:
                logger.debug(f"Error finding dropdown items on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await page.wait_for_timeout(DELAY_MEDIUM)
        
        if not year_items:
            logger.error("Could not find any dropdown items after clicking dropdown button")
            # Try to take a screenshot or get page HTML for debugging
            try:
                page_html = await page.content()
                if EARNINGS_YEAR_DROPDOWN_ITEM.replace('[', '').replace(']', '') in page_html:
                    logger.debug("Dropdown items exist in DOM but may not be visible")
            except:
                pass
            return False
        
        # Find and click the year option
        available_years = []
        for item in year_items:
            try:
                # Try to get the label text directly from the item or its child
                label_element = await item.query_selector(EARNINGS_YEAR_DROPDOWN_LABEL)
                if label_element:
                    label_text = await label_element.text_content()
                else:
                    # Fallback: try to get text directly from the button
                    label_text = await item.text_content()
                
                if label_text:
                    label_text = label_text.strip()
                    available_years.append(label_text)
                    logger.debug(f"Found dropdown item with text: '{label_text}'")
                    if label_text == year:
                        # Scroll item into view if needed
                        await item.scroll_into_view_if_needed()
                        await page.wait_for_timeout(DELAY_SHORT)
                        await item.click()
                        await page.wait_for_timeout(DELAY_LONG)  # Wait for page to update
                        logger.info(f"Successfully selected year {year}")
                        return True
            except Exception as e:
                logger.debug(f"Error checking year item: {e}")
                continue
        
        logger.warning(f"Year {year} not found in dropdown. Available items: {available_years}")
        return False
        
    except Exception as e:
        logger.error(f"Error selecting year {year}: {e}")
        return False

# ------------------------------ END OF FILE ------------------------------
