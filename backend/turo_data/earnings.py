# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import Page

from utils.logger import logger
from .selectors import (
    BUSINESS_EARNINGS_URL, EARNINGS_TOTAL_SELECTOR, EARNINGS_TOTAL_TEXT_SELECTOR,
    EARNINGS_LEGEND_SELECTOR, EARNINGS_LEGEND_TAG_SELECTOR, EARNINGS_AMOUNT_SELECTOR,
    EARNINGS_TYPE_SELECTOR, EARNINGS_TOOLTIP_SELECTOR, VEHICLE_EARNINGS_HEADER_SELECTOR,
    VEHICLE_EARNINGS_ROW_SELECTOR, VEHICLE_EARNINGS_IMAGE_SELECTOR, VEHICLE_EARNINGS_NAME_SELECTOR,
    VEHICLE_EARNINGS_DETAILS_SELECTOR, VEHICLE_EARNINGS_AMOUNT_SELECTOR
)

# ------------------------------ EARNINGS PAGE SCRAPING ------------------------------

async def navigate_to_earnings_page(page: Page):
    """
    Navigate to the business earnings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        bool: True if navigation successful, Otherwise False.
    """
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

async def extract_total_earnings(page: Page):
    """
    Extract total earnings amount and text from the earnings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing total earnings amount and full text
    """
    try:
        total_earnings = {
            'amount': None,
            'text': None,
            'year': None
        }
        
        amount_element = await page.query_selector(EARNINGS_TOTAL_SELECTOR)
        if amount_element:
            amount_text = await amount_element.text_content()
            if amount_text:
                total_earnings['amount'] = amount_text.strip()
        
        text_element = await page.query_selector(EARNINGS_TOTAL_TEXT_SELECTOR)
        if text_element:
            full_text = await text_element.text_content()
            if full_text:
                total_earnings['text'] = full_text.strip()
                import re
                year_match = re.search(r'earned\s+in\s+(\d{4})', full_text)
                if year_match:
                    total_earnings['year'] = year_match.group(1)
        
        return total_earnings
        
    except Exception as e:
        logger.debug(f"Error extracting total earnings: {e}")
        return {'amount': None, 'text': None, 'year': None}

async def extract_earnings_breakdown(page: Page):
    """
    Extract earnings breakdown by type from the legend section.
    
    Args:
        page: Playwright page object.
        
    Returns:
        list: List of dictionaries containing earnings type data
    """
    try:
        earnings_breakdown = []
        
        await page.wait_for_selector(EARNINGS_LEGEND_SELECTOR, timeout=10000)
        
        legend_tags = await page.query_selector_all(EARNINGS_LEGEND_TAG_SELECTOR)
        
        for tag in legend_tags:
            try:
                amount_element = await tag.query_selector(EARNINGS_AMOUNT_SELECTOR)
                amount = None
                if amount_element:
                    amount_text = await amount_element.text_content()
                    if amount_text:
                        amount = amount_text.strip()
                
                type_element = await tag.query_selector(EARNINGS_TYPE_SELECTOR)
                earnings_type = None
                if type_element:
                    type_text = await type_element.text_content()
                    if type_text:
                        earnings_type = type_text.strip()
                
                tooltip_element = await tag.query_selector(EARNINGS_TOOLTIP_SELECTOR)
                description = None
                if tooltip_element:
                    tooltip_text = await tooltip_element.text_content()
                    if tooltip_text:
                        description = tooltip_text.strip()
                
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
        
    except Exception as e:
        logger.debug(f"Error extracting earnings breakdown: {e}")
        return []

async def extract_vehicle_earnings(page: Page):
    """
    Extract vehicle-specific earnings from the earnings table.
    
    Args:
        page: Playwright page object.
        
    Returns:
        list: List of dictionaries containing vehicle earnings data
    """
    try:
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
                if name_element:
                    name_text = await name_element.text_content()
                    if name_text:
                        vehicle_data['vehicle_name'] = name_text.strip()
                
                details_element = await row.query_selector(VEHICLE_EARNINGS_DETAILS_SELECTOR)
                if details_element:
                    details_text = await details_element.text_content()
                    if details_text:
                        lines = details_text.strip().split('\n')
                        if len(lines) >= 1:
                            vehicle_data['license_plate'] = lines[0].strip()
                        if len(lines) >= 2:
                            vehicle_data['trim'] = lines[1].strip()
                
                amount_element = await row.query_selector(VEHICLE_EARNINGS_AMOUNT_SELECTOR)
                if amount_element:
                    amount_text = await amount_element.text_content()
                    if amount_text:
                        vehicle_data['earnings_amount'] = amount_text.strip()
                
                vehicle_earnings.append(vehicle_data)
                logger.info(f"Scraped vehicle earnings {i+1}: {vehicle_data['vehicle_name']} - {vehicle_data['earnings_amount']}")
                
            except Exception as e:
                logger.debug(f"Error extracting vehicle earnings row {i}: {e}")
                continue
        
        return vehicle_earnings
        
    except Exception as e:
        logger.debug(f"Error extracting vehicle earnings: {e}")
        return []

async def scrape_earnings_data(page: Page):
    """
    Scrape all earnings data from the business earnings page.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing all earnings data, or None if failed.
    """
    try:
        logger.info("Starting to scrape earnings data...")
        
        if not await navigate_to_earnings_page(page):
            logger.error("Failed to navigate to earnings page")
            return None
        
        total_earnings = await extract_total_earnings(page)
        
        earnings_breakdown = await extract_earnings_breakdown(page)
        
        vehicle_earnings = await extract_vehicle_earnings(page)
        
        total_breakdown_amount = 0
        for item in earnings_breakdown:
            try:
                amount_str = item['amount'].replace('$', '').replace(',', '')
                total_breakdown_amount += float(amount_str)

            except:
                continue
        
        earnings_data = {
            'total_earnings': total_earnings,
            'earnings_breakdown': earnings_breakdown,
            'vehicle_earnings': vehicle_earnings,
            'summary': {
                'total_vehicles': len(vehicle_earnings),
                'total_breakdown_amount': total_breakdown_amount,
                'scraped_at': None
            }
        }
        
        logger.info("Earnings data scraping completed successfully!")
        return earnings_data
        
    except Exception as e:
        logger.exception(f"Error scraping earnings data: {e}")
        return None

# ------------------------------ COMBINED EARNINGS SCRAPING ------------------------------

async def scrape_all_earnings_data(page: Page):
    """
    Scrape all earnings data including totals, breakdown, and vehicle earnings.
    
    Args:
        page: Playwright page object.
        
    Returns:
        dict: Dictionary containing all earnings data, or None if failed.
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
                'summary': {'total_vehicles': 0, 'total_breakdown_amount': 0, 'scraped_at': None}
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
