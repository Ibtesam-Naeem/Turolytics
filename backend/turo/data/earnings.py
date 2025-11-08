# ------------------------------ IMPORTS ------------------------------
import asyncio
from datetime import datetime
from typing import Optional, Any
from playwright.async_api import Page

from core.utils.logger import logger
from .helpers import navigate_to_page, extract_with_regex, get_text, process_items_in_parallel, parse_amount
from .selectors import (
    BUSINESS_EARNINGS_URL, EARNINGS_TOTAL_SELECTOR, EARNINGS_TOTAL_TEXT_SELECTOR,
    EARNINGS_LEGEND_SELECTOR, EARNINGS_LEGEND_TAG_SELECTOR, EARNINGS_AMOUNT_SELECTOR,
    EARNINGS_TYPE_SELECTOR, VEHICLE_EARNINGS_HEADER_SELECTOR,
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

def parse_license_plate_and_trim(details_text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse license plate and trim from details text (format: "LICENSE_PLATE • TRIM")."""
    if not details_text:
        return None, None
    
    parts = details_text.split(' • ')
    license_plate = parts[0].strip()
    trim = parts[1].strip() if len(parts) > 1 else None
    return license_plate, trim

# ------------------------------ EARNINGS PAGE SCRAPING ------------------------------

async def extract_total_earnings(page: Page) -> dict[str, Optional[str]]:
    """Extract total earnings amount and year from the earnings page."""
    try:
        await page.wait_for_selector(EARNINGS_TOTAL_TEXT_SELECTOR, timeout=10000)
        
        amount = await get_text(page, EARNINGS_TOTAL_SELECTOR)
        full_text = await get_text(page, EARNINGS_TOTAL_TEXT_SELECTOR)
        
        if not amount and full_text:
            amount = extract_with_regex(full_text, r'\$[\d,]+\.?\d*')
        
        year = extract_with_regex(full_text or '', r'earned\s+in\s+(\d{4})') if full_text else None
        
        return {
            'amount': amount,
            'year': year
        }
    except Exception as e:
        logger.debug(f"Error extracting total earnings: {e}")
        return {'amount': None, 'year': None}

async def extract_earnings_breakdown_item(tag, tag_index: int) -> Optional[dict[str, Optional[str]]]:
    """Extract earnings breakdown data from a single legend tag."""
    try:
        amount = await get_text(tag, EARNINGS_AMOUNT_SELECTOR)
        earnings_type = await get_text(tag, EARNINGS_TYPE_SELECTOR)
        
        if amount and earnings_type:
            return {
                'type': earnings_type,
                'amount': amount
            }
        return None
    except Exception as e:
        logger.debug(f"Error extracting earnings breakdown item {tag_index}: {e}")
        return None

async def extract_earnings_breakdown(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract earnings breakdown by type from the legend section using parallel processing."""
    try:
        await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=10000)
        legend_tags = await page.query_selector_all(EARNINGS_LEGEND_TAG_SELECTOR)
        
        breakdown = await process_items_in_parallel(
            legend_tags,
            extract_earnings_breakdown_item,
            item_type="earnings breakdown item"
        )
        
        return breakdown
    except Exception as e:
        logger.debug(f"Error extracting earnings breakdown: {e}")
        return []

async def extract_vehicle_earnings_row(row, row_index: int) -> dict[str, Optional[str]]:
    """Extract earnings data from a single vehicle earnings row."""
    try:
        vehicle_name = await get_text(row, VEHICLE_EARNINGS_NAME_SELECTOR)
        details_text = await get_text(row, VEHICLE_EARNINGS_DETAILS_SELECTOR)
        earnings_amount = await get_text(row, VEHICLE_EARNINGS_AMOUNT_SELECTOR)
        
        license_plate, trim = parse_license_plate_and_trim(details_text)
        
        return {
            'vehicle_name': vehicle_name,
            'license_plate': license_plate,
            'trim': trim,
            'earnings_amount': earnings_amount
        }
    except Exception as e:
        logger.debug(f"Error extracting vehicle earnings row {row_index}: {e}")
        return {
            'vehicle_name': None,
            'license_plate': None,
            'trim': None,
            'earnings_amount': None
        }

async def extract_vehicle_earnings(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract vehicle-specific earnings from the earnings table using parallel processing."""
    try:
        await page.wait_for_selector(VEHICLE_EARNINGS_HEADER_SELECTOR, timeout=10000)
        vehicle_rows = await page.query_selector_all(VEHICLE_EARNINGS_ROW_SELECTOR)
        
        vehicles = await process_items_in_parallel(
            vehicle_rows,
            extract_vehicle_earnings_row,
            item_type="vehicle earnings row"
        )
        
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
        
        total_earnings, earnings_breakdown, vehicle_earnings = await asyncio.gather(
            extract_total_earnings(page),
            extract_earnings_breakdown(page),
            extract_vehicle_earnings(page)
        )
        
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

# ------------------------------ END OF FILE ------------------------------