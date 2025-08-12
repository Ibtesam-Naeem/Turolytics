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
