# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
from typing import Optional, Any, List
from datetime import datetime

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text
from core.utils.data_helpers import parse_amount
from .helpers import navigate_to_page, extract_with_regex
from .selectors import (
    BUSINESS_EARNINGS_URL, EARNINGS_TOTAL_SELECTOR, EARNINGS_TOTAL_TEXT_SELECTOR,
    EARNINGS_LEGEND_SELECTOR, EARNINGS_LEGEND_TAG_SELECTOR, EARNINGS_AMOUNT_SELECTOR,
    EARNINGS_TYPE_SELECTOR, EARNINGS_TOOLTIP_SELECTOR, VEHICLE_EARNINGS_HEADER_SELECTOR,
    VEHICLE_EARNINGS_ROW_SELECTOR, VEHICLE_EARNINGS_NAME_SELECTOR,
    VEHICLE_EARNINGS_DETAILS_SELECTOR, VEHICLE_EARNINGS_AMOUNT_SELECTOR
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def build_summary(vehicle_earnings: list, earnings_breakdown: list) -> dict[str, Any]:
    """Build summary data for earnings."""
    return {
        'total_vehicles': len(vehicle_earnings),
        'total_breakdown_amount': sum(
            parse_amount(item['amount'])
            for item in earnings_breakdown if item.get('amount')
        ) or 0,
        'scraped_at': datetime.utcnow().isoformat()
    }

# ------------------------------ EARNINGS PAGE SCRAPING ------------------------------

async def extract_total_earnings(page: Page) -> dict[str, Optional[str]]:
    """Extract total earnings amount and text from the earnings page."""
    try:
        # Wait for the total earnings element to be available
        await page.wait_for_selector(EARNINGS_TOTAL_TEXT_SELECTOR, timeout=10000)
        
        amount_element = await page.query_selector(EARNINGS_TOTAL_SELECTOR)
        amount = await safe_text(amount_element)
        
        text_element = await page.query_selector(EARNINGS_TOTAL_TEXT_SELECTOR)
        full_text = await safe_text(text_element)
        
        # If we got the text but not the amount, try to extract amount from text
        if not amount and full_text:
            # Try to extract amount using regex from the full text
            amount_match = extract_with_regex(full_text, r'\$[\d,]+\.?\d*')
            if amount_match:
                amount = amount_match
        
        year = extract_with_regex(full_text or '', r'earned\s+in\s+(\d{4})') if full_text else None
        
        logger.debug(f"Extracted total earnings - amount: {amount}, text: {full_text[:50] if full_text else None}, year: {year}")
        
        return {
            'amount': amount,
            'text': full_text,
            'year': year
        }
    except Exception as e:
        logger.warning(f"Error extracting total earnings: {e}")
        return {'amount': None, 'text': None, 'year': None}

async def extract_earnings_breakdown(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract earnings breakdown by type from the legend section."""
    try:
        await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=10000)
        legend_tags = await page.query_selector_all(EARNINGS_LEGEND_TAG_SELECTOR)
        
        breakdown = []
        for tag in legend_tags:
            try:
                amount_element = await tag.query_selector(EARNINGS_AMOUNT_SELECTOR)
                amount = await safe_text(amount_element)
                
                type_element = await tag.query_selector(EARNINGS_TYPE_SELECTOR)
                earnings_type = await safe_text(type_element)
                
                description_element = await tag.query_selector(EARNINGS_TOOLTIP_SELECTOR)
                description = await safe_text(description_element)
                
                if amount and earnings_type:
                    breakdown.append({
                        'type': earnings_type,
                        'amount': amount,
                        'description': description
                    })
            except Exception:
                continue
        
        return breakdown
    except Exception as e:
        logger.debug(f"Error extracting earnings breakdown: {e}")
        return []

async def extract_vehicle_earnings(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract vehicle-specific earnings from the earnings table."""
    try:
        await page.wait_for_selector(VEHICLE_EARNINGS_HEADER_SELECTOR, timeout=10000)
        vehicle_rows = await page.query_selector_all(VEHICLE_EARNINGS_ROW_SELECTOR)
        
        vehicles = []
        for i, row in enumerate(vehicle_rows):
            try:
                name_element = await row.query_selector(VEHICLE_EARNINGS_NAME_SELECTOR)
                vehicle_name = await safe_text(name_element)
                
                details_element = await row.query_selector(VEHICLE_EARNINGS_DETAILS_SELECTOR)
                details_text = await safe_text(details_element)
                
                # Parse license plate and trim from details text
                # Format is typically: "LICENSE_PLATE • TRIM" or just "LICENSE_PLATE"
                license_plate = None
                trim = None
                
                if details_text:
                    # Split by " • " to separate license plate and trim
                    parts = details_text.split(' • ')
                    if len(parts) >= 1:
                        license_plate = parts[0].strip()
                    if len(parts) >= 2:
                        trim = parts[1].strip()
                
                amount_element = await row.query_selector(VEHICLE_EARNINGS_AMOUNT_SELECTOR)
                earnings_amount = await safe_text(amount_element)
                
                vehicle_data = {
                    'vehicle_name': vehicle_name,
                    'license_plate': license_plate,
                    'trim': trim,
                    'earnings_amount': earnings_amount
                }
                
                vehicles.append(vehicle_data)
                logger.debug(f"Scraped vehicle earnings {i+1}: {vehicle_data['vehicle_name']} - {vehicle_data['earnings_amount']}")
            except Exception as e:
                logger.debug(f"Error extracting vehicle earnings row {i}: {e}")
                continue
        
        return vehicles
    except Exception as e:
        logger.debug(f"Error extracting vehicle earnings: {e}")
        return []

async def scrape_earnings_data(page: Page) -> Optional[dict[str, Any]]:
    """Scrape earnings data from the business earnings page."""
    try:
        logger.info("Starting to scrape earnings data...")
        
        if not await navigate_to_page(page, BUSINESS_EARNINGS_URL, "Business Earnings"):
            logger.error("Failed to navigate to earnings page")
            return None
        
        total_earnings = await extract_total_earnings(page)
        earnings_breakdown = await extract_earnings_breakdown(page)
        vehicle_earnings = await extract_vehicle_earnings(page)
        
        earnings_data = {
            'total_earnings': total_earnings,
            'earnings_breakdown': earnings_breakdown,
            'vehicle_earnings': vehicle_earnings,
            'summary': build_summary(vehicle_earnings, earnings_breakdown)
        }
        
        logger.info("Earnings data scraping completed successfully!")
        return earnings_data
    except Exception as e:
        logger.exception(f"Error scraping earnings data: {e}")
        return None

# ------------------------------ COMBINED EARNINGS SCRAPING ------------------------------

async def scrape_all_earnings_data(page: Page) -> Optional[dict[str, Any]]:
    """Scrape all earnings data including totals, breakdown, and vehicle earnings."""
    try:
        logger.info("Starting to scrape all earnings data...")
        
        earnings_data = await scrape_earnings_data(page)
        if not earnings_data:
            logger.warning("Failed to scrape earnings data")
            earnings_data = {
                'total_earnings': {'amount': None, 'text': None, 'year': None},
                'earnings_breakdown': [],
                'vehicle_earnings': [],
                'summary': build_summary([], [])
            }
        
        all_earnings_data = {
            'earnings': earnings_data,
            'scraping_success': {'earnings': earnings_data is not None}
        }
        
        logger.info("All earnings data scraping completed!")
        return all_earnings_data
    except Exception as e:
        logger.exception(f"Error scraping all earnings data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------

