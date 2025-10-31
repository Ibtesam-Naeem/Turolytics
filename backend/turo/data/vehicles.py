# ------------------------------ IMPORTS ------------------------------
from collections import Counter
from datetime import datetime

from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text
from .helpers import navigate_to_page
from .selectors import (
    VEHICLES_LISTINGS_URL, VEHICLES_VIEW_SELECTORS, VEHICLE_CARD,
    VEHICLES_LISTINGS_GRID_SELECTORS
)
from .extraction_helpers import extract_complete_vehicle_data

async def find_vehicle_container(page: Page) -> str | None:
    """Find the vehicle container using multiple selectors."""
    selectors = VEHICLES_VIEW_SELECTORS + VEHICLES_LISTINGS_GRID_SELECTORS + [VEHICLE_CARD]
    
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=4000)
            logger.debug(f"Vehicles container found using selector: {sel}")
            return sel
        
        except Exception:
            continue
    
    logger.error("Vehicles container not found; proceeding with best-effort scraping")
    return None

async def extract_vehicle_cards(page: Page) -> list[dict]:
    """Extract all vehicle cards data."""
    try:
        await page.wait_for_selector(VEHICLE_CARD, timeout=10000)
        vehicle_cards = await page.query_selector_all(VEHICLE_CARD)
        logger.info(f"Found {len(vehicle_cards)} vehicle cards on listings page")
        
        vehicles_list = []
        for i, card in enumerate(vehicle_cards):
            try:
                vehicle_data = await extract_complete_vehicle_data(card, i)
                vehicles_list.append(vehicle_data)
            
            except Exception as e:
                logger.debug(f"Error scraping vehicle card {i}: {e}")
                continue
        
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
        
        await find_vehicle_container(page)
        
        vehicles_list = await extract_vehicle_cards(page)
        status_counts = Counter(v.get('status') for v in vehicles_list)
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