# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page
from typing import Optional, Any, List
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

async def try_selectors(page: Page, selectors: List[str]) -> Optional[str]:
    """Try multiple selectors and return first valid result."""
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            text = await safe_text(element)
            if text:
                return text.strip()
                
        except Exception:
            continue
    return None

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    match = re.search(pattern, text)
    return match.group(group) if match else None

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
        
        success = "business/earnings" in page.url
        if success:
            logger.info("Successfully navigated to Business Earnings page")
        else:
            logger.warning(f"Navigation may have failed. Current URL: {page.url}")
        return success
    except Exception as e:
        logger.exception(f"Error navigating to Business Earnings: {e}")
        return False

@safe_scrape({'amount': None, 'text': None, 'year': None})
async def extract_total_earnings(page: Page) -> dict[str, Optional[str]]:
    """Extract total earnings amount and text from the earnings page."""
    amount_element = await page.query_selector(EARNINGS_TOTAL_SELECTOR)
    amount = await safe_text(amount_element)
    
    text_element = await page.query_selector(EARNINGS_TOTAL_TEXT_SELECTOR)
    full_text = await safe_text(text_element)
    
    year = extract_with_regex(full_text or '', r'earned\s+in\s+(\d{4})') if full_text else None
    
    return {
        'amount': amount,
        'text': full_text,
        'year': year
    }

@safe_scrape([])
async def extract_earnings_breakdown(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract earnings breakdown by type from the legend section."""
    await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=10000)
    legend_tags = await page.query_selector_all(EARNINGS_LEGEND_TAG_SELECTOR)
    
    breakdown = []
    for tag in legend_tags:
        try:
            amount = await safe_text(await tag.query_selector(EARNINGS_AMOUNT_SELECTOR))
            earnings_type = await safe_text(await tag.query_selector(EARNINGS_TYPE_SELECTOR))
            description = await safe_text(await tag.query_selector(EARNINGS_TOOLTIP_SELECTOR))
            
            if amount and earnings_type:
                breakdown.append({
                    'type': earnings_type,
                    'amount': amount,
                    'description': description
                })
        except Exception:
            continue
    
    return breakdown

@safe_scrape([])
async def extract_vehicle_earnings(page: Page) -> list[dict[str, Optional[str]]]:
    """Extract vehicle-specific earnings from the earnings table."""
    await page.wait_for_selector(VEHICLE_EARNINGS_HEADER_SELECTOR, timeout=10000)
    vehicle_rows = await page.query_selector_all(VEHICLE_EARNINGS_ROW_SELECTOR)
    
    vehicles = []
    for i, row in enumerate(vehicle_rows):
        try:
            image_element = await row.query_selector(VEHICLE_EARNINGS_IMAGE_SELECTOR)
            details_text = await safe_text(await row.query_selector(VEHICLE_EARNINGS_DETAILS_SELECTOR))
            
            lines = details_text.split('\n') if details_text else []
            
            vehicle_data = {
                'vehicle_name': await safe_text(await row.query_selector(VEHICLE_EARNINGS_NAME_SELECTOR)),
                'license_plate': lines[0].strip() if len(lines) >= 1 else None,
                'trim': lines[1].strip() if len(lines) >= 2 else None,
                'earnings_amount': await safe_text(await row.query_selector(VEHICLE_EARNINGS_AMOUNT_SELECTOR)),
                'image_url': await image_element.get_attribute('src') if image_element else None,
                'image_alt': await image_element.get_attribute('alt') if image_element else None
            }
            
            vehicles.append(vehicle_data)
            logger.debug(f"Scraped vehicle earnings {i+1}: {vehicle_data['vehicle_name']} - {vehicle_data['earnings_amount']}")
        except Exception:
            continue
    
    return vehicles

async def scrape_earnings_data(page: Page) -> Optional[dict[str, Any]]:
    """Scrape earnings data from the business earnings page."""
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