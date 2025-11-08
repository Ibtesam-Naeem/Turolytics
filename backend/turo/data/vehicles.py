# ------------------------------ IMPORTS ------------------------------
import re
from datetime import datetime
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text
from .selectors import (
    VEHICLES_LISTINGS_URL, VEHICLES_VIEW_SELECTORS, VEHICLE_CARD, VEHICLE_LISTINGS_COUNT_SELECTORS,
    VEHICLES_LISTINGS_GRID_SELECTORS
)
from .extraction_helpers import extract_complete_vehicle_data

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def find_vehicle_container(page: Page) -> str | None:
    """Find the vehicle container using multiple selectors."""
    selectors = VEHICLES_VIEW_SELECTORS + VEHICLES_LISTINGS_GRID_SELECTORS + [VEHICLE_CARD]
    
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=4000)
            logger.info(f"Vehicles container found using selector: {sel}")
            return sel
        except Exception:
            continue
    
    logger.error("Vehicles container not found; proceeding with best-effort scraping")
    return None

def extract_listings_count(count_text: str) -> int:
    """Extract total listings count from text."""
    if not count_text:
        return 0
    
    count_match = re.search(r'(\d+)\s*Listings?', count_text)
    return int(count_match.group(1)) if count_match else 0

async def extract_vehicle_cards_data(page: Page) -> list[dict]:
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
                
                vehicle_name = vehicle_data.get('name', 'N/A')
                vehicle_status = vehicle_data.get('status', 'N/A')
                logger.info(f"Scraped vehicle {i+1}: {vehicle_data.get('vehicle_id')} - {vehicle_status} - {vehicle_name}")
            except Exception as e:
                logger.warning(f"Error scraping vehicle card {i}: {e}")
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
        
        logger.info("Navigating to Vehicle Listings page...")
        await page.goto(VEHICLES_LISTINGS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        await find_vehicle_container(page)
        
        count_element = await page.query_selector(VEHICLE_LISTINGS_COUNT_SELECTORS[0])
        count_text = await safe_text(count_element)
        total_listings = extract_listings_count(count_text)
        if total_listings > 0:
            logger.info(f"Found {total_listings} vehicle listings")
        
        vehicles_list = await extract_vehicle_cards_data(page)
        
        listed_vehicles = [v for v in vehicles_list if v.get('status') == 'Listed']
        snoozed_vehicles = [v for v in vehicles_list if v.get('status') == 'Snoozed']
        other_status_vehicles = [v for v in vehicles_list if v.get('status') not in ['Listed', 'Snoozed']]
        
        vehicle_listings_data = {
            "vehicles": vehicles_list,
            "total_vehicles": len(vehicles_list),
            "total_listings": total_listings,
            "listed_vehicles": len(listed_vehicles),
            "snoozed_vehicles": len(snoozed_vehicles),
            "other_status_vehicles": len(other_status_vehicles),
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Vehicle listings scraping completed successfully!")
        return vehicle_listings_data

    except Exception as e:
        logger.exception(f"Error scraping vehicle listings: {e}")
        return None

# ------------------------------ VEHICLE DETAILS SCRAPING ------------------------------

async def scrape_vehicle_details(page: Page, vehicle_id: str):
    """Scrape detailed information for a specific vehicle."""
    try:
        logger.info(f"Starting to scrape details for vehicle {vehicle_id}...")
        
        vehicle_details_url = f"https://turo.com/ca/en/your-car/{vehicle_id}"
        await page.goto(vehicle_details_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        vehicle_details = {
            "vehicle_id": vehicle_id,
            "details_url": vehicle_details_url,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Vehicle details scraping completed for vehicle {vehicle_id}")
        return vehicle_details

    except Exception as e:
        logger.exception(f"Error scraping vehicle details for {vehicle_id}: {e}")
        return None

# ------------------------------ COMBINED VEHICLE SCRAPING ------------------------------

async def scrape_all_vehicle_data(page: Page):
    """Scrape all vehicle data including listings and any additional information."""
    try:
        logger.info("Starting to scrape all vehicle data...")
        
        listings_data = await scrape_vehicle_listings(page)
        if not listings_data:
            logger.warning("Failed to scrape vehicle listings data")
            listings_data = {
                "vehicles": [], "total_vehicles": 0, "total_listings": 0,
                "listed_vehicles": 0, "snoozed_vehicles": 0, "other_status_vehicles": 0, "scraped_at": None
            }
        
        all_vehicle_data = {
            "listings": listings_data,
            "scraping_success": {"listings": listings_data is not None}
        }
        
        logger.info("All vehicle data scraping completed!")
        return all_vehicle_data

    except Exception as e:
        logger.exception(f"Error scraping all vehicle data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------