# ------------------------------ IMPORTS ------------------------------
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import scroll_to_bottom_and_wait
from core.config.settings import TIMEOUT_SELECTOR_WAIT
from .helpers import navigate_to_page, process_items_in_parallel, get_text, extract_texts_from_elements, count_statuses, scraping_function
from .selectors import (
    TRIPS_BOOKED_URL, TRIPS_HISTORY_URL,
    TRIPS_UPCOMING_LIST, TRIP_HISTORY_LIST, TRIP_CARD,
    DATE_HEADER_SELECTORS, TIME_INFO, LOCATION
)
from .extraction_helpers import extract_complete_trip_data, extract_month_headers, extract_complete_trip_detail_data

EMPTY_BOOKED = {"trips": [], "total_trips": 0, "dates": [], "scraped_at": None}
EMPTY_HISTORY = {"trips": [], "total_trips": 0, "completed_trips": 0, "cancelled_trips": 0, "months": [], "scraped_at": None}

async def extract_trip_cards_data(page: Page, card_selector: str, list_selector: str, page_name: str, existing_trip_ids: set[str] = None) -> list[dict]:
    """Generic function to extract trip cards data using parallel processing.
    
    Args:
        page: Playwright page object
        card_selector: CSS selector for trip cards
        list_selector: CSS selector for the list container
        page_name: Name of the page for logging
        existing_trip_ids: Set of trip_ids that already exist in database (to skip)
    """
    if existing_trip_ids is None:
        existing_trip_ids = set()
    
    try:
        await page.wait_for_selector(list_selector, timeout=TIMEOUT_SELECTOR_WAIT)
        trip_cards = await page.query_selector_all(card_selector)
        logger.debug(f"Found {len(trip_cards)} trip cards on {page_name}")
        
        trips_list = await process_items_in_parallel(
            trip_cards,
            extract_complete_trip_data,
            item_type=f"{page_name} trip card"
        )
        
        # Filter out trips we already have
        new_trips = [trip for trip in trips_list if trip.get('trip_id') not in existing_trip_ids]
        skipped_count = len(trips_list) - len(new_trips)
        
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} already-scraped trips on {page_name}, processing {len(new_trips)} new trips")
        elif len(new_trips) > 0:
            logger.info(f"Processing {len(new_trips)} new trips on {page_name}")
        
        return new_trips

    except Exception as e:
        logger.exception(f"Error extracting {page_name} trip cards: {e}")
        return []

# ------------------------------ BOOKED TRIPS SCRAPING ------------------------------

@scraping_function("booked trips")
async def scrape_booked_trips(page: Page, existing_trip_ids: set[str] = None): 
    """Scrape all booked/upcoming trips data from the booked trips page.
    
    Args:
        page: Playwright page object
        existing_trip_ids: Set of trip_ids that already exist in database (to skip)
    """
    if existing_trip_ids is None:
        existing_trip_ids = set()
    
    if not await navigate_to_page(page, TRIPS_BOOKED_URL, "Booked Trips"):
        logger.error("Failed to navigate to booked trips page")
        return None
    
    trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIPS_UPCOMING_LIST, "booked", existing_trip_ids)
    
    location_text = await get_text(page, LOCATION)
    time_text = await get_text(page, TIME_INFO)
    dates_list = []
    for selector in DATE_HEADER_SELECTORS:
        dates_list = await extract_texts_from_elements(page, selector)
        if dates_list:
            break
    
    return {
        "trips": trips_list,
        "total_trips": len(trips_list),
        "dates": dates_list,
        "location": location_text,
        "time_info": time_text,
        "scraped_at": datetime.utcnow().isoformat()
    }

# ------------------------------ DETAILED TRIP EXTRACTION ------------------------------

async def enrich_trips_with_details(page: Page, trips_list: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
    """Enrich trip data by visiting each trip detail page in batches to avoid bot detection."""
    if not trips_list:
        return []
    
    enriched_trips = []
    total_trips = len(trips_list)
    context = page.context
    
    logger.info(f"Starting to enrich {total_trips} trips with detailed data (batch size: {batch_size})...")
    
    for i in range(0, total_trips, batch_size):
        batch = trips_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_trips + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} trips)...")
        
        batch_tasks = []
        valid_trips = []
        
        async def process_trip_with_page(trip_url: str, trip_data: Dict[str, Any]):
            """Process a single trip using a new page."""
            new_page = None
            try:
                new_page = await context.new_page()
                detail_data = await extract_complete_trip_detail_data(new_page, trip_url)
                return {**trip_data, **detail_data}
            
            except Exception as e:
                logger.error(f"Error enriching trip {trip_data.get('trip_id', 'unknown')}: {e}")
                return trip_data
            
            finally:
                if new_page:
                    try:
                        await new_page.close()
                    except Exception:
                        pass
        
        for trip in batch:
            trip_url = trip.get('trip_url')
            if not trip_url:
                logger.warning(f"Trip {trip.get('trip_id', 'unknown')} missing trip_url, skipping")
                enriched_trips.append(trip)
                continue
            
            if trip_url.startswith('/'):
                trip_url = f"https://turo.com{trip_url}"
            
            valid_trips.append(trip)
            batch_tasks.append(process_trip_with_page(trip_url, trip))
        
        if batch_tasks:
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for trip_data, result in zip(valid_trips, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing for trip {trip_data.get('trip_id', 'unknown')}: {result}")
                    enriched_trips.append(trip_data)
                else:
                    enriched_trips.append(result)
        
        if i + batch_size < total_trips:
            await asyncio.sleep(2)
    
    logger.info(f"Successfully enriched {len(enriched_trips)} trips with detailed data")
    return enriched_trips

# ------------------------------ HISTORY TRIPS SCRAPING -----------------------------
@scraping_function("trip history")
async def scrape_trip_history(page: Page, include_details: bool = True, existing_trip_ids: set[str] = None):
    """Scrape all completed trips data from the trip history page.
    
    Args:
        page: Playwright page object
        include_details: Whether to enrich trips with detailed data
        existing_trip_ids: Set of trip_ids that already exist in database (to skip)
    """
    if existing_trip_ids is None:
        existing_trip_ids = set()
    
    if not await navigate_to_page(page, TRIPS_HISTORY_URL, "Trip History"):
        logger.error("Failed to navigate to trip history page")
        return None
    
    await scroll_to_bottom_and_wait(page)
    
    trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIP_HISTORY_LIST, "history", existing_trip_ids)
    
    if include_details and trips_list:
        trips_list = await enrich_trips_with_details(page, trips_list, batch_size=3)
    
    months_list = await extract_month_headers(page)
    
    status_counts = count_statuses(trips_list, status_key='status')
    
    total_earnings = 0.0
    trips_with_earnings = 0
    for trip in trips_list:
        earnings = trip.get('earnings', {}).get('total_earnings')
        if earnings is not None:
            total_earnings += earnings
            trips_with_earnings += 1
    
    return {
        "trips": trips_list,
        "total_trips": len(trips_list),
        "completed_trips": status_counts.get('COMPLETED', 0),
        "cancelled_trips": status_counts.get('CANCELLED', 0),
        "months": months_list,
        "total_earnings": total_earnings if trips_with_earnings > 0 else None,
        "trips_with_earnings": trips_with_earnings,
        "scraped_at": datetime.utcnow().isoformat()
    }

# ------------------------------ COMBINED TRIPS SCRAPING ------------------------------

@scraping_function("all trips")
async def scrape_all_trips(page: Page, existing_trip_ids: set[str] = None):
    """Scrape both booked trips and trip history data.
    
    Args:
        page: Playwright page object
        existing_trip_ids: Set of trip_ids that already exist in database (to skip)
    """
    if existing_trip_ids is None:
        existing_trip_ids = set()
    
    booked_data = await scrape_booked_trips(page, existing_trip_ids=existing_trip_ids)
    booked_success = booked_data is not None
    if not booked_data:
        logger.warning("Failed to scrape booked trips data")
        booked_data = EMPTY_BOOKED.copy()
    
    history_data = await scrape_trip_history(page, existing_trip_ids=existing_trip_ids)
    history_success = history_data is not None
    if not history_data:
        logger.warning("Failed to scrape trip history data")
        history_data = EMPTY_HISTORY.copy()
    
    return {
        "booked_trips": booked_data,
        "trip_history": history_data,
        "scraping_success": {
            "booked": booked_success,
            "history": history_success
        }
    }

# ------------------------------ END OF FILE ------------------------------