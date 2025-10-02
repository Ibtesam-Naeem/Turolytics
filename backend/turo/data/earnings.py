# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
from typing import Optional, Any
from datetime import datetime
import re

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text, safe_scrape
from core.utils.data_helpers import parse_amount
from .selectors import (
    BUSINESS_EARNINGS_URL, EARNINGS_TOTAL_SELECTOR, EARNINGS_TOTAL_TEXT_SELECTOR,
    EARNINGS_LEGEND_SELECTOR, EARNINGS_LEGEND_TAG_SELECTOR, EARNINGS_AMOUNT_SELECTOR,
    EARNINGS_TYPE_SELECTOR, EARNINGS_TOOLTIP_SELECTOR, VEHICLE_EARNINGS_HEADER_SELECTOR,
    VEHICLE_EARNINGS_ROW_SELECTOR, VEHICLE_EARNINGS_IMAGE_SELECTOR, VEHICLE_EARNINGS_NAME_SELECTOR,
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
        ),
        'scraped_at': datetime.utcnow().isoformat()
    }

# ------------------------------ EARNINGS PAGE SCRAPING ------------------------------

async def navigate_to_earnings_page(page: Page) -> bool:
    """Navigate to the business earnings page."""
    try:
        logger.info("Navigating to Business Earnings page...")
        await page.goto(BUSINESS_EARNINGS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        if "business/earnings" in page.url:
            logger.info("Successfully navigated to Business Earnings page")
            return True
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
            return False
            
    except Exception as e:
        logger.exception(f"Error navigating to Business Earnings: {e}")
        return False

@safe_scrape({'amount': None, 'text': None, 'year': None})
async def extract_total_earnings(page: Page) -> dict[str, Optional[str]]:
    """Extract total earnings amount and text from the earnings page."""
    total_earnings = {
        'amount': None,
        'text': None,
        'year': None
    }
    
    amount_element = await page.query_selector(EARNINGS_TOTAL_SELECTOR)
    total_earnings['amount'] = await safe_text(amount_element)
    
    text_element = await page.query_selector(EARNINGS_TOTAL_TEXT_SELECTOR)
    full_text = await safe_text(text_element)
    
    if full_text:
        total_earnings['text'] = full_text
        year_match = re.search(r'earned\s+in\s+(\d{4})', full_text)
        if year_match:
            total_earnings['year'] = year_match.group(1)
    
    return total_earnings

@safe_scrape([])
async def extract_earnings_breakdown(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract earnings breakdown by type from the legend section."""
    earnings_breakdown = []
    
    await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=10000)
    
    legend_tags = await page.query_selector_all(EARNINGS_LEGEND_TAG_SELECTOR)
    
    for tag in legend_tags:
        try:
            amount_element = await tag.query_selector(EARNINGS_AMOUNT_SELECTOR)
            amount = await safe_text(amount_element)
            
            type_element = await tag.query_selector(EARNINGS_TYPE_SELECTOR)
            earnings_type = await safe_text(type_element)
            
            tooltip_element = await tag.query_selector(EARNINGS_TOOLTIP_SELECTOR)
            description = await safe_text(tooltip_element)
            
            if amount and earnings_type:
                earnings_breakdown.append({
                    'type': earnings_type,
                    'amount': amount,
                    'description': description
                })
                
        except Exception as e:
            logger.debug(f"Error extracting earnings breakdown item: {e}")
            continue
    
    return earnings_breakdown

@safe_scrape([])
async def extract_vehicle_earnings(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract vehicle-specific earnings from the earnings table."""
    vehicle_earnings = []
    
    await page.wait_for_selector(VEHICLE_EARNINGS_HEADER_SELECTOR, timeout=10000)
    
    vehicle_rows = await page.query_selector_all(VEHICLE_EARNINGS_ROW_SELECTOR)
    
    for i, row in enumerate(vehicle_rows):
        try:
            vehicle_data = {
                'vehicle_name': None,
                'license_plate': None,
                'trim': None,
                'earnings_amount': None,
                'image_url': None,
                'image_alt': None
            }
            
            image_element = await row.query_selector(VEHICLE_EARNINGS_IMAGE_SELECTOR)

            if image_element:
                vehicle_data['image_url'] = await image_element.get_attribute('src')
                vehicle_data['image_alt'] = await image_element.get_attribute('alt')
            
            name_element = await row.query_selector(VEHICLE_EARNINGS_NAME_SELECTOR)
            vehicle_data['vehicle_name'] = await safe_text(name_element)
            
            details_element = await row.query_selector(VEHICLE_EARNINGS_DETAILS_SELECTOR)
            details_text = await safe_text(details_element)

            if details_text:
                lines = details_text.split('\n')
                if len(lines) >= 1:
                    vehicle_data['license_plate'] = lines[0].strip()
                if len(lines) >= 2:
                    vehicle_data['trim'] = lines[1].strip()
            
            amount_element = await row.query_selector(VEHICLE_EARNINGS_AMOUNT_SELECTOR)
            vehicle_data['earnings_amount'] = await safe_text(amount_element)
            
            vehicle_earnings.append(vehicle_data)
            logger.debug(f"Scraped vehicle earnings {i+1}: {vehicle_data['vehicle_name']} - {vehicle_data['earnings_amount']}")
            
        except Exception as e:
            logger.debug(f"Error extracting vehicle earnings row {i}: {e}")
            continue
    
    return vehicle_earnings

async def scrape_earnings_data(page: Page) -> Optional[dict[str, Any]]:
    """
    Scrape earnings data from the business earnings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        Dictionary containing all earnings data, or None if failed.
    """
    try:
        logger.info("Starting to scrape earnings data...")
        
        if not await navigate_to_earnings_page(page):
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
    """
    Scrape all earnings data including totals, breakdown, and vehicle earnings.
    
    Args:
        page: Playwright page object.
        
    Returns:
        Dictionary containing all earnings data, or None if failed.
    """
    try:
        logger.info("Starting to scrape all earnings data...")
        
        earnings_data = await scrape_earnings_data(page)
        if not earnings_data:
            logger.warning("Failed to scrape earnings data")
            
        all_earnings_data = {
            'earnings': earnings_data if earnings_data else {
                'total_earnings': {'amount': None, 'text': None, 'year': None},
                'earnings_breakdown': [],
                'vehicle_earnings': [],
                'summary': build_summary([], [])
            },
            'scraping_success': {
                'earnings': earnings_data is not None
            }
        }
        
        logger.info("All earnings data scraping completed!")
        return all_earnings_data
        
    except Exception as e:
        logger.exception(f"Error scraping all earnings data: {e}")
        return None

# ------------------------------ END OF FILE ------------------------------