# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page, Frame

# ------------------------------ BROWSER HELPER FUNCTIONS ------------------------------
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
