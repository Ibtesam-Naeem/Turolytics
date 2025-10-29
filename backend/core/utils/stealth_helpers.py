# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
import random
import time
from typing import List, Dict, Optional
from core.utils.logger import logger

# ------------------------------ STEALTH UTILITIES ------------------------------

class StealthHelper:
    """Helper class for implementing stealth behaviors."""
    
    @staticmethod
    async def random_mouse_movement(page: Page) -> None:
        """Simulate random mouse movements."""
        try:
            viewport = page.viewport_size
            if not viewport:
                return
                
            for _ in range(random.randint(2, 5)):
                x = random.randint(0, viewport["width"])
                y = random.randint(0, viewport["height"])
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(100, 300))
        except Exception as e:
            logger.debug(f"Mouse movement failed: {e}")
    
    @staticmethod
    async def random_scroll(page: Page) -> None:
        """Simulate random scrolling behavior."""
        try:
            scroll_amount = random.randint(100, 500)
            scroll_direction = random.choice([-1, 1])
            
            await page.mouse.wheel(0, scroll_amount * scroll_direction)
            await page.wait_for_timeout(random.randint(200, 800))
        except Exception as e:
            logger.debug(f"Scroll failed: {e}")
    
    @staticmethod
    async def simulate_human_behavior(page: Page) -> None:
        """Simulate various human-like behaviors."""
        behaviors = [
            StealthHelper.random_mouse_movement,
            StealthHelper.random_scroll,
        ]
        
        num_behaviors = random.randint(1, 3)
        selected_behaviors = random.sample(behaviors, min(num_behaviors, len(behaviors)))
        
        for behavior in selected_behaviors:
            await behavior(page)
            await page.wait_for_timeout(random.randint(500, 1500))

# ------------------------------ PROXY CONFIGURATION ------------------------------

def create_proxy_config(proxy_url: str, username: Optional[str] = None, password: Optional[str] = None) -> Dict:
    """Create proxy configuration for Playwright."""
    config = {"server": proxy_url}
    
    if username and password:
        config["username"] = username
        config["password"] = password
    
    return config

# ------------------------------ CAPTCHA DETECTION ------------------------------

async def detect_captcha(page: Page) -> bool:
    """Detect if a CAPTCHA is present on the page."""
    captcha_selectors = [
        "iframe[src*='recaptcha']",
        ".g-recaptcha",
        "#captcha",
        ".captcha",
        "iframe[src*='hcaptcha']",
        ".h-captcha",
        "[data-sitekey]"
    ]
    
    for selector in captcha_selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                logger.warning("CAPTCHA detected on page")
                return True
        except Exception:
            continue
    
    return False

# ------------------------------ BROWSER FINGERPRINT EVASION ------------------------------

def get_random_fingerprint() -> Dict:
    """Generate random browser fingerprint data."""
    return {
        "screen_resolution": random.choice([
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]),
        "timezone": random.choice([
            "America/New_York",
            "America/Los_Angeles", 
            "America/Chicago",
            "Europe/London",
            "Europe/Paris"
        ]),
        "language": random.choice([
            "en-US",
            "en-GB",
            "en-CA"
        ]),
        "platform": random.choice([
            "MacIntel",
            "Win32",
            "Linux x86_64"
        ])
    }

# ------------------------------ SESSION MANAGEMENT ------------------------------

class SessionManager:
    """Manage browser sessions with stealth features."""
    
    def __init__(self):
        self.active_sessions = {}
    
    async def create_stealth_session(self, page: Page, session_id: str) -> None:
        """Create a new stealth session."""
        self.active_sessions[session_id] = {
            "page": page,
            "created_at": time.time(),
            "fingerprint": get_random_fingerprint()
        }
        logger.info(f"Created stealth session: {session_id}")
    
    async def rotate_session_fingerprint(self, session_id: str) -> None:
        """Rotate fingerprint for existing session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["fingerprint"] = get_random_fingerprint()
            logger.info(f"Rotated fingerprint for session: {session_id}")

# ------------------------------ END OF FILE ------------------------------

