# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page

from utils.logger import logger
from .selectors import (
    TRIPS_BOOKED_URL, TRIPS_HISTORY_URL,
    TRIPS_UPCOMING_LIST, TRIP_HISTORY_LIST, TRIP_CARD,
    DATE_HEADER, TIME_INFO, LOCATION
)
from .extraction_helpers import extract_complete_trip_data, extract_month_headers

# ------------------------------ BOOKED TRIPS SCRAPING ------------------------------

async def navigate_to_booked_trips(page: Page):
    """
    Navigate to the booked trips page under the Trips section.
    
    Args:
        page: Playwright page object.
        
    Returns:
        bool: True if navigation successful, Otherwise False.
    """
    try:
        logger.info("Navigating to Trips -> Booked page...")
        await page.goto(TRIPS_BOOKED_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        if "trips/booked" in page.url:
            logger.info("Successfully navigated to Trips -> Booked page")
            return True
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
            return False
            
    except Exception as e:
        logger.exception(f"Error navigating to Trips -> Booked: {e}")
        return False

async def scrape_booked_trips(page: Page):
    """
    Scrape all booked/upcoming trips data from the booked trips page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing booked trips data, or None if failed.
    """
    try:
        logger.info("Starting to scrape booked trips data...")
        
        if not await navigate_to_booked_trips(page):
            logger.error("Failed to navigate to booked trips page")
            return None
            
        await page.wait_for_selector(TRIPS_UPCOMING_LIST, timeout=10000)
        
        trip_cards = await page.query_selector_all(TRIP_CARD)
        trips_list = []
        
        for i, card in enumerate(trip_cards):
            try:
                trip_data = await extract_complete_trip_data(card, i)
                
                try:
                    location_element = await card.query_selector(LOCATION)
                    if location_element:
                        trip_data['location'] = await location_element.text_content()
                    
                    time_element = await card.query_selector(TIME_INFO)
                    if time_element:
                        trip_data['time_info'] = await time_element.text_content()
                except:
                    pass
                
                trips_list.append(trip_data)
                logger.info(f"Scraped booked trip: {trip_data.get('trip_id', 'Unknown ID')}")
                
            except Exception as e:
                logger.warning(f"Error scraping booked trip card {i}: {e}")
                continue
        
        dates_list = []
        try:
            date_headers = await page.query_selector_all(DATE_HEADER)
            for header in date_headers:
                try:
                    date_text = await header.text_content()
                    if date_text:
                        dates_list.append(date_text)
                except:
                    continue
        except:
            pass
        
        booked_trips_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "dates": dates_list,
            "scraped_at": None
        }
        
        logger.info("Booked trips scraping completed successfully!")
        return booked_trips_data
        
    except Exception as e:
        logger.exception(f"Error scraping booked trips: {e}")
        return None

# ------------------------------ HISTORY TRIPS SCRAPING ------------------------------

async def navigate_to_trip_history(page: Page):
    """
    Navigate to the trip history page under the Trips section.
    
    Args:
        page: Playwright page object.
        
    Returns:
        bool: True if navigation successful, Otherwise False.
    """
    try:
        logger.info("Navigating to Trips -> History page...")
        await page.goto(TRIPS_HISTORY_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        if "trips/history" in page.url:
            logger.info("Successfully navigated to Trips -> History page")
            return True
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
            return False
            
    except Exception as e:
        logger.exception(f"Error navigating to Trips -> History: {e}")
        return False

async def scrape_trip_history(page: Page):
    """
    Scrape all completed trips data from the trip history page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing trip history data, or None if failed.
    """
    try:
        logger.info("Starting to scrape trip history data...")
        
        if not await navigate_to_trip_history(page):
            logger.error("Failed to navigate to trip history page")
            return None
            
        await page.wait_for_selector(TRIP_HISTORY_LIST, timeout=10000)
        
        await page.wait_for_timeout(3000)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
        except:
            pass
        
        trip_cards = await page.query_selector_all(TRIP_CARD)
        logger.info(f"Found {len(trip_cards)} trip cards on history page")
        
        trips_list = []
        
        for i, card in enumerate(trip_cards):
            try:
                trip_data = await extract_complete_trip_data(card, i)
                trips_list.append(trip_data)
                
                customer_name = trip_data.get('customer_name', 'N/A')
                logger.info(f"Scraped history trip {i+1}: {trip_data.get('trip_id')} - "
                          f"{trip_data.get('status')} - {customer_name}")
                
            except Exception as e:
                logger.warning(f"Error scraping history trip card {i}: {e}")
                continue
        
        months_list = await extract_month_headers(page)
        
        completed_trips = [trip for trip in trips_list if trip.get('status') == 'completed']
        cancelled_trips = [trip for trip in trips_list if trip.get('status') == 'cancelled']
        
        trip_history_data = {
            "trips": trips_list,
            "total_trips": len(trips_list),
            "completed_trips": len(completed_trips),
            "cancelled_trips": len(cancelled_trips),
            "months": months_list,
            "scraped_at": None
        }
        
        logger.info("Trip history scraping completed successfully!")
        return trip_history_data
        
    except Exception as e:
        logger.exception(f"Error scraping trip history: {e}")
        return None

# ------------------------------ COMBINED TRIPS SCRAPING ------------------------------

async def scrape_all_trips(page: Page):
    """
    Scrape both booked trips and trip history data.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing all trips data, or None if failed.
    """
    try:
        logger.info("Starting to scrape all trips data...")
        
        booked_data = await scrape_booked_trips(page)
        if not booked_data:
            logger.warning("Failed to scrape booked trips data")
            
        history_data = await scrape_trip_history(page)
        if not history_data:
            logger.warning("Failed to scrape trip history data")
            
        all_trips_data = {
            "booked_trips": booked_data if booked_data else {"trips": [], "total_trips": 0},
            "trip_history": history_data if history_data else {"trips": [], "total_trips": 0},
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
