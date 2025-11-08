# ------------------------------ IMPORTS ------------------------------
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import Page

from core.utils.logger import logger
from core.utils.browser_helpers import scroll_to_bottom_and_wait
from .helpers import navigate_to_page, process_items_in_parallel, get_text, extract_texts_from_elements, count_statuses
from .selectors import (
    TRIPS_BOOKED_URL, TRIPS_HISTORY_URL,
    TRIPS_UPCOMING_LIST, TRIP_HISTORY_LIST, TRIP_CARD,
    DATE_HEADER_SELECTORS, TIME_INFO, LOCATION
)
from .extraction_helpers import extract_complete_trip_data, extract_month_headers, extract_complete_trip_detail_data

EMPTY_BOOKED = {"trips": [], "total_trips": 0, "dates": [], "scraped_at": None}
EMPTY_HISTORY = {"trips": [], "total_trips": 0, "completed_trips": 0, "cancelled_trips": 0, "months": [], "scraped_at": None}

async def extract_trip_cards_data(page: Page, card_selector: str, list_selector: str, page_name: str) -> list[dict]:
    """Generic function to extract trip cards data using parallel processing."""
    try:
        await page.wait_for_selector(list_selector, timeout=10000)
        trip_cards = await page.query_selector_all(card_selector)
        logger.debug(f"Found {len(trip_cards)} trip cards on {page_name}")
        
        trips_list = await process_items_in_parallel(
            trip_cards,
            extract_complete_trip_data,
            item_type=f"{page_name} trip card"
        )
        
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
        
        location_text = await get_text(page, LOCATION)
        time_text = await get_text(page, TIME_INFO)
        dates_list = []
        for selector in DATE_HEADER_SELECTORS:
            dates_list = await extract_texts_from_elements(page, selector)
            if dates_list:
                break
        
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

# ------------------------------ DETAILED TRIP EXTRACTION ------------------------------

async def enrich_trips_with_details(page: Page, trips_list: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
    """Enrich trip data by visiting each trip detail page in batches to avoid bot detection."""
    if not trips_list:
        return []
    
    enriched_trips = []
    total_trips = len(trips_list)
    context = page.context
    
    logger.info(f"Starting to enrich {total_trips} trips with detailed data (batch size: {batch_size})...")
    
    # Process trips in batches
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
async def scrape_trip_history(page: Page, include_details: bool = True):
    """Scrape all completed trips data from the trip history page."""
    try:
        logger.info("Starting to scrape trip history data...")
        
        if not await navigate_to_page(page, TRIPS_HISTORY_URL, "Trip History"):
            logger.error("Failed to navigate to trip history page")
            return None
        
        await scroll_to_bottom_and_wait(page)
        
        trips_list = await extract_trip_cards_data(page, TRIP_CARD, TRIP_HISTORY_LIST, "history")
        
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
        
        trip_history_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "completed_trips": status_counts.get('COMPLETED', 0),
            "cancelled_trips": status_counts.get('CANCELLED', 0),
            "months": months_list,
            "total_earnings": total_earnings if trips_with_earnings > 0 else None,
            "trips_with_earnings": trips_with_earnings,
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
        booked_success = booked_data is not None
        if not booked_data:
            logger.warning("Failed to scrape booked trips data")
            booked_data = EMPTY_BOOKED.copy()
        
        history_data = await scrape_trip_history(page)
        history_success = history_data is not None
        if not history_data:
            logger.warning("Failed to scrape trip history data")
            history_data = EMPTY_HISTORY.copy()
        
        all_trips_data = {
            "booked_trips": booked_data,
            "trip_history": history_data,
            "scraping_success": {
                "booked": booked_success,
                "history": history_success
            }
        }
        
        logger.info("All trips data scraping completed!")
        return all_trips_data

    except Exception as e:
        logger.exception(f"Error scraping all trips data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------