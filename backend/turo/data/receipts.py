# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from playwright.async_api import Page

from core.config.settings import TIMEOUT_PAGE_LOAD, DELAY_SHORT
from .helpers import scraping_function
from .extraction_helpers import extract_receipt_data
from turo.service import get_receipt_url

logger = logging.getLogger(__name__)

# ------------------------------ RECEIPT SCRAPING ------------------------------

@scraping_function("receipts")
async def scrape_receipts_data(page: Page, trip_ids: List[str] = None, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Scrape receipt data for given trip IDs.
    
    Args:
        page: Playwright page object
        trip_ids: List of trip IDs to scrape receipts for. If None, returns None.
        batch_size: Number of receipts to scrape in parallel (default: 5)
    
    Returns:
        Dictionary with receipt data keyed by trip_id
    """
    if not trip_ids:
        logger.warning("No trip IDs provided for receipt scraping")
        return None
    
    logger.info(f"Starting receipt scraping for {len(trip_ids)} trips (batch size: {batch_size})...")
    
    receipts_data = {}
    context = page.context
    
    # Process in batches to avoid overwhelming the browser
    for i in range(0, len(trip_ids), batch_size):
        batch = trip_ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(trip_ids) + batch_size - 1) // batch_size
        
        logger.info(f"Processing receipt batch {batch_num}/{total_batches} ({len(batch)} receipts)...")
        
        batch_tasks = []
        
        async def process_receipt(trip_id: str):
            """Process a single receipt using a new page."""
            new_page = None
            try:
                new_page = await context.new_page()
                receipt_url = get_receipt_url(trip_id)
                receipt_data = await extract_receipt_data(new_page, receipt_url)
                # Ensure reservation_id is set (use trip_id if not already set)
                if receipt_data and 'reservation_id' not in receipt_data:
                    receipt_data['reservation_id'] = trip_id
                
                # Small delay before closing to ensure data is fully processed
                await asyncio.sleep(0.5)
                
                return trip_id, receipt_data
            except Exception as e:
                logger.error(f"Error scraping receipt for trip {trip_id}: {e}")
                return trip_id, {'error': str(e)}
            finally:
                if new_page:
                    try:
                        # Small delay before closing page
                        await asyncio.sleep(0.3)
                        await new_page.close()
                    except Exception:
                        pass
        
        # Process batch in parallel
        for trip_id in batch:
            batch_tasks.append(process_receipt(trip_id))
        
        if batch_tasks:
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {result}")
                    continue
                
                trip_id, receipt_data = result
                if receipt_data and 'error' not in receipt_data:
                    receipts_data[trip_id] = receipt_data
                    logger.debug(f"Successfully scraped receipt for trip {trip_id}")
                else:
                    logger.warning(f"Failed to scrape receipt for trip {trip_id}: {receipt_data.get('error', 'Unknown error')}")
        
        # Delay between batches to avoid rate limiting
        if i + batch_size < len(trip_ids):
            await asyncio.sleep(2)  # 2 second delay between batches
    
    logger.info(f"Successfully scraped {len(receipts_data)} receipts out of {len(trip_ids)} trips")
    
    if not receipts_data:
        logger.warning("No receipt data was scraped")
        return None
    
    return {
        'receipts': receipts_data,
        'total_receipts': len(receipts_data),
        'scraped_at': datetime.utcnow().isoformat()
    }

# ------------------------------ END OF FILE ------------------------------
