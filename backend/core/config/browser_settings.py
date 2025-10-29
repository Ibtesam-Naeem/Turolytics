# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import async_playwright, Page, BrowserContext, Browser
from typing import Optional, List
import random
import time
from core.utils.logger import logger

# ------------------------------ CONFIGURATION ------------------------------
from core.config.settings import settings
USER_AGENT = settings.scraping.user_agent

DEFAULT_VIEWPORT = {"width": 1366, "height": 768}
DEFAULT_TIMEOUT = 30000
DEFAULT_HEADLESS = False

BROWSER_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--disable-ipc-flooding-protection",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--disable-client-side-phishing-detection",
    "--disable-sync",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--disable-javascript",
    "--disable-plugins-discovery",
    "--disable-preconnect",
    "--disable-translate",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-logging",
    "--disable-gpu-logging",
    "--silent",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-component-extensions-with-background-pages",
]

ANTI_DETECTION_SCRIPT = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Override the plugins property to use a custom getter
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Override the languages property to use a custom getter
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Override the permissions property
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Remove automation indicators
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

// Override chrome property
Object.defineProperty(window, 'chrome', {
    get: () => ({
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {}
    })
});

// Mock screen properties
Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
Object.defineProperty(screen, 'height', { get: () => 1080 });
Object.defineProperty(screen, 'width', { get: () => 1920 });

// Mock timezone
Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
    value: function() {
        return { timeZone: 'America/New_York' };
    }
});

// Override Date.getTimezoneOffset
Date.prototype.getTimezoneOffset = function() {
    return 300; // EST timezone offset
};
"""

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720}
]

# ------------------------------ HELPER FUNCTIONS ------------------------------
def get_random_user_agent() -> str:
    """Get a random user agent from the pool."""
    return random.choice(USER_AGENTS)

def get_random_viewport() -> dict[str, int]:
    """Get a random viewport from the pool."""
    return random.choice(VIEWPORTS)

def get_random_delay(min_ms: int = 100, max_ms: int = 500) -> float:
    """Get a random delay in seconds for human-like behavior."""
    return random.uniform(min_ms / 1000, max_ms / 1000)

async def human_like_delay(page: Page, min_ms: int = 100, max_ms: int = 500) -> None:
    """Add a human-like delay before performing actions."""
    delay = get_random_delay(min_ms, max_ms)
    await page.wait_for_timeout(int(delay * 1000))

async def human_like_click(page: Page, selector: str) -> bool:
    """Perform a human-like click with random delay."""
    try:
        await human_like_delay(page, 200, 800)
        await page.click(selector)
        await human_like_delay(page, 100, 300)
        return True
    
    except Exception as e:
        logger.warning(f"Failed to click {selector}: {e}")
        return False

async def human_like_type(page: Page, selector: str, text: str) -> bool:
    """Perform human-like typing with random delays."""
    try:
        await human_like_delay(page, 200, 500)
        await page.click(selector)
        await human_like_delay(page, 100, 200)
        
        for char in text:
            await page.keyboard.type(char)
            await page.wait_for_timeout(random.randint(50, 150))
        
        await human_like_delay(page, 100, 300)
        return True
    
    except Exception as e:
        logger.warning(f"Failed to type in {selector}: {e}")
        return False

# ------------------------------ VALIDATION FUNCTIONS ------------------------------
def validate_viewport(viewport: dict[str, int]) -> bool:
    """Validate viewport dimensions."""
    return (isinstance(viewport, dict) and 
            all(k in viewport for k in ("width", "height")) and
            all(isinstance(viewport[k], int) and viewport[k] > 0 for k in ("width", "height")))

def validate_user_agent(user_agent: str) -> bool:
    """Validate user agent string."""
    return isinstance(user_agent, str) and bool(user_agent.strip())

# ------------------------------ BROWSER LAUNCH FUNCTION ------------------------------
async def launch_browser(
    headless: bool = DEFAULT_HEADLESS,
    user_agent: Optional[str] = None,
    viewport: Optional[dict[str, int]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    storage_state_path: Optional[str] = None,
    proxy: Optional[dict] = None,
    randomize_fingerprint: bool = True,
) -> tuple[Page, BrowserContext, Browser]:
    """
    Launches a Chromium browser with enhanced stealth settings.
    
    Args:
        headless: Whether to run the browser in headless mode.
        user_agent: The user agent string to use. If None, uses random selection.
        viewport: The viewport size for the browser context. If None, uses random selection.
        timeout: Timeout in milliseconds for page operations.
        storage_state_path: Optional path to storage state file for session restoration.
        proxy: Optional proxy configuration dict with 'server' key.
        randomize_fingerprint: Whether to randomize browser fingerprint.
        
    Returns:
        A tuple containing (page, context, browser) objects.
        
    Raises:
        ValueError: If input parameters are invalid.
        Exception: If browser launch or context creation fails.
    """
    
    if randomize_fingerprint:
        user_agent = user_agent or get_random_user_agent()
        viewport = viewport or get_random_viewport()
    else:
        user_agent = user_agent or USER_AGENT
        viewport = viewport or DEFAULT_VIEWPORT
    
    if not validate_user_agent(user_agent):
        raise ValueError("Invalid user agent string provided")
    
    if not validate_viewport(viewport):
        raise ValueError("Invalid viewport configuration provided")
    
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("Timeout must be a positive integer")
    
    browser = None
    playwright = None
    
    try:
        logger.info("Starting stealth browser launch...")
        playwright = await async_playwright().start()
        
        logger.debug(f"Launching Chromium browser (headless: {headless}, fingerprint: {randomize_fingerprint})")
        
        context_options = {
            "user_agent": user_agent,
            "viewport": viewport,
            "storage_state": storage_state_path,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},  # NYC coordinates
            "permissions": ["geolocation"],
            "extra_http_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        }
        
        if proxy:
            context_options["proxy"] = proxy
        
        browser = await playwright.chromium.launch(
            headless=headless,
            args=BROWSER_LAUNCH_ARGS,
        )
        
        context = await browser.new_context(**context_options)
        
        page = await context.new_page()
        page.set_default_timeout(timeout)
        
        await page.add_init_script(ANTI_DETECTION_SCRIPT)
        
        await page.add_init_script("""
            // Override getParameter to hide automation
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return originalGetParameter(parameter);
            };
            
            // Override canvas fingerprinting
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    context.fillStyle = 'rgba(255, 255, 255, 0.01)';
                    context.fillRect(0, 0, 1, 1);
                }
                return originalToDataURL.apply(this, arguments);
            };
        """)
        
        logger.info("Stealth browser launched successfully")
        return page, context, browser

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")

        if browser:
            try:
                await browser.close()
                logger.info("Browser closed successfully")
            except Exception:
                pass

        if playwright:
            try:
                await playwright.stop()
                logger.info("Playwright stopped successfully")
            except Exception:
                pass
        raise

# ------------------------------ END OF FILE ------------------------------
