# ------------------------------ IMPORTS ------------------------------
import re
from typing import Optional, List, Any, Union, Dict
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
    """Try multiple selectors and return first valid result.
    
    Args:
        element: Page or ElementHandle to query
        selectors: List of CSS selectors to try
        validator: Optional function to validate the extracted text
        
    Returns:
        First valid text found, or None if none match
    """
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
    """Get text from an element using a selector.
    
    Args:
        element: Page or ElementHandle to query
        selector: CSS selector to find the element
        
    Returns:
        Text content if found, None otherwise
    """
    target = await element.query_selector(selector)
    return await safe_text(target)

# ------------------------------ NAVIGATION HELPERS ------------------------------

async def navigate_to_page(page: Page, url: str, page_name: str) -> bool:
    """Generic navigation function for Turo pages.
    
    Args:
        page: Playwright page object
        url: URL to navigate to
        page_name: Human-readable name for logging
        
    Returns:
        True if navigation successful, False otherwise
    """
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
    """
    Get the iframe content frame for Turo login forms.

    Args:
        page: Playwright page object.
        timeout: Timeout in milliseconds for iframe selector.

    Returns:
        Frame: The iframe content frame, or None if not found.
    """
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
    """
    Search for specific error messages on the page and in iframe.
    
    Args:
        page: Playwright page object
        iframe_content: Iframe content frame if available
        error_messages: List of error messages to search for. If None, uses default Turo-specific errors.
        
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

async def clear_form_inputs(page: Page, input_selectors: List[str], iframe_content: Optional[Frame] = None) -> None:
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
        
    except Exception:
        return False

# ------------------------------ VEHICLE DATA EXTRACTION ------------------------------

def extract_vehicle_info(vehicle_name: str) -> Dict[str, Optional[str]]:
    """Extract year, make, model from Turo vehicle name string.
    
    Args:
        vehicle_name: Raw vehicle name string from Turo UI
        
    Returns:
        Dict with 'full_name', 'year', 'make', 'model' keys
    """
    if not vehicle_name:
        return {"full_name": None, "year": None, "make": None, "model": None}
    
    cleaned_name = vehicle_name
    
    status_prefixes = ['Snoozed', 'Listed', 'Unavailable', 'Maintenance']
    for prefix in status_prefixes:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix):].strip()
            break

    extra_patterns = [
        r' • [A-Z0-9]+.*',  
        r'No trips.*',       
        r'Vehicle actions.*', 
        r'Last trip:.*',     
    ]
    
    for pattern in extra_patterns:
        cleaned_name = re.sub(pattern, '', cleaned_name).strip()
    
    parts = cleaned_name.split()
    if len(parts) >= 3:
        year = None
        year_index = -1
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4 and 1900 <= int(part) <= 2030:
                year = int(part)
                year_index = i
                break
        
        if year is not None:
            if year_index == 0: 
                make = parts[1] if len(parts) > 1 else None
                model = ' '.join(parts[2:]) if len(parts) > 2 else None
            elif year_index == len(parts) - 1: 
                make = parts[0] if len(parts) > 1 else None
                model = ' '.join(parts[1:year_index]) if year_index > 1 else None
            else:  
                make = parts[0] if year_index > 0 else None
                model = ' '.join(parts[year_index+1:]) if year_index < len(parts) - 1 else None
            
            return {
                "full_name": f"{make} {model} {year}".strip() if make and model else cleaned_name,
                "year": year,
                "make": make,
                "model": model
            }
    
    # Fallback: try to extract year from anywhere in the string
    year_match = re.search(r'\b(19|20)\d{2}\b', cleaned_name)
    if year_match:
        year = int(year_match.group())
        without_year = re.sub(r'\b(19|20)\d{2}\b', '', cleaned_name).strip()
        parts = without_year.split()
        if len(parts) >= 2:
            make = parts[0]
            model = ' '.join(parts[1:])
            return {
                "full_name": f"{make} {model} {year}".strip(),
                "year": year,
                "make": make,
                "model": model
            }
    
    return {"full_name": cleaned_name, "year": None, "make": None, "model": None}

