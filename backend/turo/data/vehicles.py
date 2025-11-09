# ------------------------------ IMPORTS ------------------------------
from datetime import datetime

from playwright.async_api import Page

from core.utils.logger import logger
from core.config.settings import TIMEOUT_SELECTOR_WAIT
from .helpers import navigate_to_page, process_items_in_parallel, count_statuses
from .selectors import (
    VEHICLES_LISTINGS_URL, VEHICLE_CARD
)
from .extraction_helpers import extract_complete_vehicle_data

async def extract_vehicle_cards(page: Page) -> list[dict]:
    """Extract all vehicle cards data using parallel processing when threshold is met."""
    try:
        await page.wait_for_selector(VEHICLE_CARD, timeout=TIMEOUT_SELECTOR_WAIT)
        vehicle_cards = await page.query_selector_all(VEHICLE_CARD)
        logger.info(f"Found {len(vehicle_cards)} vehicle cards on listings page")
        
        vehicles_list = await process_items_in_parallel(
            vehicle_cards,
            extract_complete_vehicle_data,
            item_type="vehicle card",
            parallel_threshold=5
        )
        
        return vehicles_list

    except Exception as e:
        logger.exception(f"Error extracting vehicle cards: {e}")
        return []

# ------------------------------ VEHICLE LISTINGS SCRAPING ------------------------------

async def scrape_vehicle_listings(page: Page):
    """Scrape all vehicle listings data from the vehicle listings page."""
    try:
        logger.info("Starting to scrape vehicle listings data...")
        
        if not await navigate_to_page(page, VEHICLES_LISTINGS_URL, "Vehicle Listings"):
            logger.error("Failed to navigate to vehicle listings page")
            return None
        
        vehicles_list = await extract_vehicle_cards(page)
        status_counts = count_statuses(vehicles_list, status_key='status')
        listed_vehicles = status_counts.get('Listed', 0)
        snoozed_vehicles = status_counts.get('Snoozed', 0)
        
        vehicle_listings_data = {
            "vehicles": vehicles_list,
            "total_vehicles": len(vehicles_list),
            "listed_vehicles": listed_vehicles,
            "snoozed_vehicles": snoozed_vehicles,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Vehicle listings scraping completed successfully!")
        return vehicle_listings_data

    except Exception as e:
        logger.exception(f"Error scraping vehicle listings: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------