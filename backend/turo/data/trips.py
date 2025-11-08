# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import scroll_to_bottom_and_wait, safe_text
from .selectors import (
    TRIPS_BOOKED_URL, TRIPS_HISTORY_URL,
    TRIPS_UPCOMING_LIST, TRIP_HISTORY_LIST, TRIP_CARD,
    DATE_HEADER_SELECTORS, TIME_INFO, LOCATION
)
from .extraction_helpers import extract_complete_trip_data, extract_month_headers

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def extract_trip_cards_data(page: Page, card_selector: str, list_selector: str, page_name: str) -> list[dict]:
    """Generic function to extract trip cards data."""
    try:
        await page.wait_for_selector(list_selector, timeout=10000)
        trip_cards = await page.query_selector_all(card_selector)
        logger.info(f"Found {len(trip_cards)} trip cards on {page_name}")
        
        trips_list = []
        for i, card in enumerate(trip_cards):
            try:
                trip_data = await extract_complete_trip_data(card, i)
                trips_list.append(trip_data)
                
                trip_id = trip_data.get('trip_id', 'Unknown ID')
                customer_name = trip_data.get('customer_name', 'N/A')
                status = trip_data.get('status', 'N/A')
                logger.info(f"Scraped {page_name} trip {i+1}: {trip_id} - {status} - {customer_name}")
            
            except Exception as e:
                logger.warning(f"Error scraping {page_name} trip card {i}: {e}")
                continue
        
        return trips_list

    except Exception as e:
        logger.exception(f"Error extracting {page_name} trip cards: {e}")
        return []

# ------------------------------ BOOKED TRIPS SCRAPING ------------------------------

async def scrape_booked_trips(page: Page):
    """Scrape all booked/upcoming trips data from the booked trips page."""
    try:
        logger.info("Starting to scrape booked trips data...")
        
        logger.info("Navigating to Trips -> Booked page...")
        await page.goto(TRIPS_BOOKED_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIPS_UPCOMING_LIST, "booked")
        
        for trip_data in trips_list:
            location_element = await page.query_selector(LOCATION)
            if location_element:
                trip_data['location'] = await safe_text(location_element)
            
            time_element = await page.query_selector(TIME_INFO)
            if time_element:
                trip_data['time_info'] = await safe_text(time_element)
        
        date_headers = await page.query_selector_all(DATE_HEADER_SELECTORS[0])
        dates_list = [await safe_text(header) for header in date_headers if await safe_text(header)]
        
        booked_trips_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "dates": dates_list,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Booked trips scraping completed successfully!")
        return booked_trips_data

    except Exception as e:
        logger.exception(f"Error scraping booked trips: {e}")
        return None

# ------------------------------ HISTORY TRIPS SCRAPING ------------------------------

async def scrape_trip_history(page: Page):
    """Scrape all completed trips data from the trip history page."""
    try:
        logger.info("Starting to scrape trip history data...")
        
        logger.info("Navigating to Trips -> History page...")
        await page.goto(TRIPS_HISTORY_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        await scroll_to_bottom_and_wait(page)
        
        trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIP_HISTORY_LIST, "history")
        
        months_list = await extract_month_headers(page)
        
        completed_trips = [trip for trip in trips_list if trip.get('status') == 'completed']
        cancelled_trips = [trip for trip in trips_list if trip.get('status') == 'cancelled']
        
        trip_history_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "completed_trips": len(completed_trips),
            "cancelled_trips": len(cancelled_trips),
            "months": months_list,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Trip history scraping completed successfully!")
        return trip_history_data

    except Exception as e:
        logger.exception(f"Error scraping trip history: {e}")
        return None

# ------------------------------ COMBINED TRIPS SCRAPING ------------------------------

async def scrape_all_trips(page: Page):
    """Scrape both booked trips and trip history data."""
    try:
        logger.info("Starting to scrape all trips data...")
        
        booked_data = await scrape_booked_trips(page)
        if not booked_data:
            logger.warning("Failed to scrape booked trips data")
            booked_data = {"trips": [], "total_trips": 0, "dates": [], "scraped_at": None}
        
        history_data = await scrape_trip_history(page)
        if not history_data:
            logger.warning("Failed to scrape trip history data")
            history_data = {"trips": [], "total_trips": 0, "completed_trips": 0, "cancelled_trips": 0, "months": [], "scraped_at": None}
        
        all_trips_data = {
            "booked_trips": booked_data,
            "trip_history": history_data,
            "scraping_success": {
                "booked": booked_data is not None,
                "history": history_data is not None
            }
        }
        
        logger.info("All trips data scraping completed!")
        return all_trips_data

    except Exception as e:
        logger.exception(f"Error scraping all trips data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------
