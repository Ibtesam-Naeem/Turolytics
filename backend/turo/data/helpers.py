# ------------------------------ IMPORTS ------------------------------
import asyncio
import re
from typing import Optional, List, Any, Union, Dict, Callable, Awaitable
from playwright.async_api import Page, ElementHandle, Frame

from core.utils.browser_helpers import safe_text
from core.utils.logger import logger

# ------------------------------ COMMON EXTRACTION HELPERS ------------------------------

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    match = re.search(pattern, text)
    return match.group(group) if match else None

def extract_number(text: str) -> Optional[float]:
    """Extract number from text using regex."""
    match = extract_with_regex(text, r'(\d+\.?\d*)')
    return float(match) if match else None

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

# ------------------------------ TURO LOGIN HELPERS ------------------------------

async def get_iframe_content(page: Page, timeout: int = 8000) -> Optional[Frame]:
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
    
    async def search_in_target(target, error_msgs):
        """Search for error messages in a given target (page or iframe)."""
        for error_msg in error_msgs:
            try:
                element = await target.query_selector(f'text="{error_msg}"')
                if element:
                    return error_msg
                    
                element = await target.query_selector(f'text*="{error_msg}"')
                if element:
                    return error_msg
            except Exception:
                continue
        return None
    
    result = await search_in_target(page, error_messages)
    if result:
        return result
    
    if iframe_content:
        result = await search_in_target(iframe_content, error_messages)
        if result:
            return result
    
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

async def clear_form_inputs(page: Page, input_selectors: List[str], iframe_content: Optional[Frame] = None) -> None:
    """Clear form input fields on form submission failure."""
    try:
        if iframe_content:
            try:
                for selector in input_selectors:
                    input_element = await iframe_content.query_selector(selector)
                    if input_element:
                        await input_element.fill('')
                await page.wait_for_timeout(500)

            except Exception:
                pass
        
        try:
            for selector in input_selectors:
                input_element = await page.query_selector(selector)
                if input_element:
                    await input_element.fill('')
            await page.wait_for_timeout(500)

        except Exception:
            pass
            
    except Exception:
        pass

async def check_for_success_element(page: Page, success_selectors: List[str], iframe_content: Optional[Frame] = None) -> bool:
    """Check if success indicators are found, indicating successful form submission."""
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
        
    except Exception:
        return False

# ------------------------------ PARALLEL PROCESSING HELPERS ------------------------------

async def process_items_in_parallel(
    items: List[Any],
    extract_func: Callable[[Any, int], Awaitable[Any]],
    item_type: str = "item"
) -> List[Any]:
    """Process multiple items (e.g., cards, elements) in parallel."""
    if not items:
        return []
    
    async def extract_with_error_handling(item: Any, index: int):
        """Extract data with error handling."""
        try:
            return await extract_func(item, index)
        except Exception as e:
            logger.debug(f"Error processing {item_type} {index}: {e}")
            return None
    
    tasks = [extract_with_error_handling(item, i) for i, item in enumerate(items)]
    results = await asyncio.gather(*tasks)
    
    return [result for result in results if result is not None]

# ------------------------------ END OF FILE ------------------------------

