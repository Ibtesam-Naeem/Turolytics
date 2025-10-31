# ------------------------------ IMPORTS ------------------------------
from collections import Counter
from datetime import datetime
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import scroll_to_bottom_and_wait, safe_text
from .helpers import navigate_to_page
from .selectors import (
    TRIPS_BOOKED_URL, TRIPS_HISTORY_URL,
    TRIPS_UPCOMING_LIST, TRIP_HISTORY_LIST, TRIP_CARD,
    DATE_HEADER_SELECTORS, TIME_INFO, LOCATION
)
from .extraction_helpers import extract_complete_trip_data, extract_month_headers

EMPTY_BOOKED = {"trips": [], "total_trips": 0, "dates": [], "scraped_at": None}
EMPTY_HISTORY = {"trips": [], "total_trips": 0, "completed_trips": 0, "cancelled_trips": 0, "months": [], "scraped_at": None}

async def extract_trip_cards_data(page: Page, card_selector: str, list_selector: str, page_name: str) -> list[dict]:
    """Generic function to extract trip cards data."""
    try:
        await page.wait_for_selector(list_selector, timeout=10000)
        trip_cards = await page.query_selector_all(card_selector)
        logger.debug(f"Found {len(trip_cards)} trip cards on {page_name}")
        
        trips_list = []
        for i, card in enumerate(trip_cards):
            try:
                trip_data = await extract_complete_trip_data(card, i)
                trips_list.append(trip_data)
           
            except Exception as e:
                logger.debug(f"Error scraping {page_name} trip card {i}: {e}")
        
        return trips_list

    except Exception as e:
        logger.exception(f"Error extracting {page_name} trip cards: {e}")
        return []

# ------------------------------ BOOKED TRIPS SCRAPING ------------------------------

async def scrape_booked_trips(page: Page): 
    """Scrape all booked/upcoming trips data from the booked trips page."""
    try:
        logger.info("Starting to scrape booked trips data...")
        
        if not await navigate_to_page(page, TRIPS_BOOKED_URL, "Booked Trips"):
            logger.error("Failed to navigate to booked trips page")
            return None
        
        trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIPS_UPCOMING_LIST, "booked")
        
        location_element = await page.query_selector(LOCATION)
        location_text = await safe_text(location_element) if location_element else None
        
        time_element = await page.query_selector(TIME_INFO)
        time_text = await safe_text(time_element) if time_element else None
        
        date_headers = await page.query_selector_all(DATE_HEADER_SELECTORS[0])
        dates_list = []
        for header in date_headers:
            text = await safe_text(header)
            if text:
                dates_list.append(text)
        
        booked_trips_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "dates": dates_list,
            "location": location_text,
            "time_info": time_text,
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
        
        if not await navigate_to_page(page, TRIPS_HISTORY_URL, "Trip History"):
            logger.error("Failed to navigate to trip history page")
            return None
        
        await scroll_to_bottom_and_wait(page)
        
        trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIP_HISTORY_LIST, "history")
        
        months_list = await extract_month_headers(page)
        
        status_counts = Counter(trip.get('status') for trip in trips_list)
        
        trip_history_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "completed_trips": status_counts.get('completed', 0),
            "cancelled_trips": status_counts.get('cancelled', 0),
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
            booked_data = EMPTY_BOOKED.copy()
        
        history_data = await scrape_trip_history(page)
        if not history_data:
            logger.warning("Failed to scrape trip history data")
            history_data = EMPTY_HISTORY.copy()
        
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
