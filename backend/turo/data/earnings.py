# ------------------------------ IMPORTS ------------------------------
import asyncio
from datetime import datetime
from typing import Optional, Any
from playwright.async_api import Page
import logging

from core.config.settings import TIMEOUT_SELECTOR_WAIT

logger = logging.getLogger(__name__)
from .helpers import navigate_to_page, extract_with_regex, get_text, process_items_in_parallel, scraping_function
from core.utils.route_helpers import parse_amount
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
    # Parse amounts and filter out None values
    amounts = [
        parse_amount(item['amount'])
        for item in earnings_breakdown if item.get('amount')
    ]
    # Filter out None values before summing
    valid_amounts = [amt for amt in amounts if amt is not None]
    
    return {
        'total_vehicles': len(vehicle_earnings),
        'total_breakdown_amount': sum(valid_amounts) if valid_amounts else 0,
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
        await page.wait_for_selector(EARNINGS_TOTAL_TEXT_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
        
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
        await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
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
        await page.wait_for_selector(VEHICLE_EARNINGS_HEADER_SELECTOR, timeout=TIMEOUT_SELECTOR_WAIT)
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

@scraping_function("earnings")
async def scrape_earnings_data(page: Page, is_initial_scrape: bool = False) -> Optional[dict[str, Any]]:
    """Scrape earnings data from the business earnings page.
    
    Args:
        page: Playwright page object
        is_initial_scrape: If True, scrape multiple years (2025, 2026). 
                          If False, only scrape current year.
    
    Returns:
        Dictionary with earnings data aggregated across all scraped years
    """
    # Determine which years to scrape
    current_year = datetime.now().year
    years_to_scrape = []
    
    if is_initial_scrape:
        # For initial scrape, scrape 2025 and 2026
        years_to_scrape = ["2025", "2026"]
        logger.info(f"Initial scrape detected - will scrape years: {years_to_scrape}")
    else:
        # For regular scrape, scrape current year and previous year (2025 and 2026)
        # This ensures we always have data for both years
        years_to_scrape = ["2025", "2026"]
        logger.info(f"Regular scrape - will scrape years: {years_to_scrape}")
    
    # Aggregate data across all years
    all_total_earnings = []
    all_earnings_breakdown = []
    all_vehicle_earnings = []
    
    for year in years_to_scrape:
        try:
            logger.info(f"Scraping earnings for year {year}...")
            
            # Navigate directly to the earnings page with year parameter
            earnings_url_with_year = f"{BUSINESS_EARNINGS_URL}?year={year}"
            logger.debug(f"Navigating to earnings URL: {earnings_url_with_year}")
            if not await navigate_to_page(page, earnings_url_with_year, f"Business Earnings ({year})"):
                logger.warning(f"Failed to navigate to earnings page for year {year}, skipping...")
                continue
            
            # Verify we're on the correct page
            current_url = page.url
            logger.debug(f"Current URL after navigation: {current_url}")
            if year not in current_url:
                logger.warning(f"URL doesn't contain year {year} - may have been redirected. Current URL: {current_url}")
            
            # Wait a bit for the page to load
            await page.wait_for_timeout(1000)
            
            # Extract data for this year
            total_earnings, earnings_breakdown, vehicle_earnings = await asyncio.gather(
                extract_total_earnings(page),
                extract_earnings_breakdown(page),
                extract_vehicle_earnings(page)
            )
            
            # Add year to breakdown items and vehicle earnings
            year_value = total_earnings.get('year') if total_earnings else year
            if year_value:
                for breakdown_item in earnings_breakdown:
                    if breakdown_item:
                        breakdown_item['year'] = year_value
                
                # Add year to vehicle earnings
                for vehicle_item in vehicle_earnings:
                    if vehicle_item:
                        vehicle_item['year'] = year_value
            
            # Log what we found for this year
            logger.info(f"Year {year} - Found {len(earnings_breakdown)} breakdown items, {len(vehicle_earnings)} vehicle earnings")
            
            # Store data for this year
            if total_earnings:
                all_total_earnings.append(total_earnings)
            if earnings_breakdown:
                all_earnings_breakdown.extend(earnings_breakdown)
            if vehicle_earnings:
                all_vehicle_earnings.extend(vehicle_earnings)
            
            logger.info(f"Successfully scraped earnings for year {year}")
            
        except Exception as e:
            logger.error(f"Error scraping earnings for year {year}: {e}")
            continue
    
    # If no data was scraped, return None
    if not all_earnings_breakdown and not all_vehicle_earnings:
        logger.warning("No earnings data was scraped from any year")
        return None
    
    # Use the most recent year's total earnings, or aggregate if needed
    final_total_earnings = all_total_earnings[-1] if all_total_earnings else None
    
    return {
        'total_earnings': final_total_earnings,
        'earnings_breakdown': all_earnings_breakdown,
        'vehicle_earnings': all_vehicle_earnings,
        'summary': build_summary(all_vehicle_earnings, all_earnings_breakdown)
    }

# ------------------------------ END OF FILE ------------------------------