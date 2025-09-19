# ------------------------------ SESSION HELPERS ------------------------------
import os
from typing import Optional

from utils.logger import logger


def get_storage_state_path():
    """
    Return absolute path to Playwright storage state JSON and ensure directory exists.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    session_dir = os.path.join(base_dir, "session")
    os.makedirs(session_dir, exist_ok=True)
    return os.path.join(session_dir, "turo_storage_state.json")


async def verify_session_authenticated(page):
    """
    Check to confirm current storage state is authenticated.
    """
    try:
        await page.goto("https://turo.com/ca/en/trips/booked", wait_until="domcontentloaded")
        await page.wait_for_timeout(800)
        await page.wait_for_url("**/trips/**", timeout=5000)
        logger.info("Session restore successful. User appears authenticated.")
        return True

    except Exception:
        logger.info("Stored session invalid or expired.")
        return False


async def save_storage_state(context):
    """
    Persist current context storage state to disk.
    """
    storage_path = get_storage_state_path()
    try:
        await context.storage_state(path=storage_path)
        logger.info(f"Saved session storage state to: {storage_path}")
        return storage_path

    except Exception as e:
        logger.warning(f"Could not save storage state: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------

