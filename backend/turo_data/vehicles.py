# ------------------------------ IMPORTS ------------------------------
import re
from datetime import datetime
from playwright.async_api import Page

from utils.logger import logger
from .selectors import (
    VEHICLES_LISTINGS_URL, VEHICLES_VIEW, VEHICLE_CARD, VEHICLE_LISTINGS_COUNT
)
from .extraction_helpers import extract_complete_vehicle_data

# ------------------------------ VEHICLE LISTINGS SCRAPING ------------------------------

async def navigate_to_vehicle_listings(page: Page):
    """
    Navigate to the vehicle listings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        bool: True if navigation successful, Otherwise False.
    """
    try:
        logger.info("Navigating to Vehicle Listings page...")
        await page.goto(VEHICLES_LISTINGS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        if "vehicles/listings" in page.url:
            logger.info("Successfully navigated to Vehicle Listings page")
            return True
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
            return False
            
    except Exception as e:
        logger.exception(f"Error navigating to Vehicle Listings: {e}")
        return False

async def scrape_vehicle_listings(page: Page):
    """
    Scrape all vehicle listings data from the vehicle listings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing vehicle listings data, or None if failed.
    """
    try:
        logger.info("Starting to scrape vehicle listings data...")
        
        if not await navigate_to_vehicle_listings(page):
            logger.error("Failed to navigate to vehicle listings page")
            return None
            
        await page.wait_for_selector(VEHICLES_VIEW, timeout=10000)
        
        total_listings = 0
        try:
            count_element = await page.query_selector(VEHICLE_LISTINGS_COUNT)
            if count_element:
                count_text = await count_element.text_content()
                if count_text:
                    count_match = re.search(r'(\d+)\s*Listings?', count_text)
                    if count_match:
                        total_listings = int(count_match.group(1))
                        logger.info(f"Found {total_listings} vehicle listings")
                        
        except:
            pass
        
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
                logger.info(f"Scraped vehicle {i+1}: {vehicle_data.get('vehicle_id')} - "
                          f"{vehicle_status} - {vehicle_name}")
                
            except Exception as e:
                logger.warning(f"Error scraping vehicle card {i}: {e}")
                continue
        
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
    """
    Scrape detailed information for a specific vehicle.
    
    Args:
        page: Playwright page object.
        vehicle_id: The ID of the vehicle to scrape details for.
        
    Returns:
        dict: Dictionary containing detailed vehicle information, or None if failed.
    """
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
    """
    Scrape all vehicle data including listings and any additional information.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing all vehicle data, or None if failed.
    """
    try:
        logger.info("Starting to scrape all vehicle data...")
        
        listings_data = await scrape_vehicle_listings(page)
        if not listings_data:
            logger.warning("Failed to scrape vehicle listings data")
            
        all_vehicle_data = {
            "listings": listings_data if listings_data else {
                "vehicles": [], 
                "total_vehicles": 0,
                "total_listings": 0,
                "listed_vehicles": 0,
                "snoozed_vehicles": 0,
                "other_status_vehicles": 0,
                "scraped_at": None
            },
            "scraping_success": {
                "listings": listings_data is not None
            }
        }
        
        logger.info("All vehicle data scraping completed!")
        return all_vehicle_data
        
    except Exception as e:
        logger.exception(f"Error scraping all vehicle data: {e}")
        return None
