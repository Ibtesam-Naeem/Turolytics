# ------------------------------ IMPORTS ------------------------------
import asyncio
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import ElementHandle, Page
import logging

from core.utils.browser_helpers import safe_text

logger = logging.getLogger(__name__)
from core.config.settings import TIMEOUT_SELECTOR_WAIT, TIMEOUT_PAGE_LOAD
from .helpers import extract_with_regex, try_selectors, get_text, extract_texts_from_elements, parse_amount
from .selectors import (
    TRIP_DATE_SELECTORS, VEHICLE_SELECTORS, CUSTOMER_SELECTORS,
    CANCELLATION_SELECTOR, LICENSE_PLATE_SELECTORS,
    MONTH_HEADER_SELECTORS,
    contains_month_name, contains_vehicle_brand,
    VEHICLE_STATUS_SELECTORS, VEHICLE_NAME_SELECTORS,
    VEHICLE_DETAILS_SELECTORS, VEHICLE_TRIP_INFO_SELECTORS, VEHICLE_RATINGS_SELECTORS,
    VALID_YEARS, VEHICLE_BRANDS, MONTH_NAMES, VEHICLE_STATUSES, YEAR_PATTERN_REGEX, YEAR_PATTERN_NON_CAPTURING,
    TRIP_DETAILS_CONTAINER, SCHEDULE_DATE_SELECTOR, SCHEDULE_TIME_START_SELECTOR, SCHEDULE_TIME_END_SELECTOR,
    LOCATION_SECTION_LABEL_SELECTOR, LOCATION_ADDRESS_SELECTOR,
    KILOMETERS_INCLUDED_SELECTOR, KILOMETERS_DRIVEN_SELECTOR, KILOMETERS_OVERAGE_SELECTOR,
    EARNINGS_AMOUNT_SELECTOR, EARNINGS_RECEIPT_LINK_SELECTOR, PROTECTION_PLAN_SELECTOR,
    PROTECTION_DEDUCTIBLE_SELECTOR, RESERVATION_NUMBER_SELECTOR
)

def parse_cancellation_from_text(raw_text: str) -> Dict[str, Optional[str]]:
    """Parse cancellation information from raw text. """
    cancellation_data = {
        'cancellation_info': None,
        'cancelled_by': None,
        'cancelled_date': None
    }
    
    if 'cancelled' not in raw_text.lower():
        return cancellation_data
    
    if ' cancelled on ' in raw_text:
        parts = raw_text.split(' cancelled on ', 1)
        before_cancelled = parts[0]
        after_cancelled = parts[1]
        

        date_match = re.search(r'([A-Z][a-z]{2}\s+\d{1,2})', after_cancelled)
        if date_match:
            cancellation_data['cancelled_date'] = date_match.group(1).strip()
        
        name_match = re.search(r'\d{4}\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+cancelled on', raw_text)
        
        if name_match:
            cancellation_data['cancelled_by'] = name_match.group(1).strip()
        else:

            cleaned = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}', '', before_cancelled)
            cleaned = re.sub(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+\d{4}', '', cleaned)
            cleaned = re.sub(r'\d{4}', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned and not cleaned.startswith(tuple(MONTH_NAMES)):
                cancellation_data['cancelled_by'] = cleaned
        
        if cancellation_data['cancelled_by'] and cancellation_data['cancelled_date']:
            cancellation_data['cancellation_info'] = f"{cancellation_data['cancelled_by']} cancelled on {cancellation_data['cancelled_date']}"
    
    return cancellation_data

# ------------------------------ CUSTOMER EXTRACTION ------------------------------

async def extract_customer_name(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract customer name from a trip card."""
    customer_text = await try_selectors(card, CUSTOMER_SELECTORS, lambda t: '#' in t)
    
    if not customer_text:
        try:
            raw_text = await card.text_content() or ''
            
            if 'cancelled' in raw_text.lower() and ' cancelled on ' in raw_text:
                cancellation_data = parse_cancellation_from_text(raw_text)
                if cancellation_data.get('cancelled_by'):
                    return cancellation_data['cancelled_by']
            
            for line in raw_text.split('\n'):
                if '#' in line and any(char.isalpha() for char in line):
                    customer_text = line.strip()
                    break

        except Exception as e:
            logger.debug(f"Error extracting customer name on card {card_index}: {e}")
    
    if customer_text:
        return customer_text.split('#')[0].strip()
    
    return None

# ------------------------------ STATUS EXTRACTION ------------------------------

async def extract_trip_status(card: ElementHandle) -> Dict[str, Any]:
    """Extract trip status and cancellation information."""
    status_data = {'status': 'COMPLETED', 'cancellation_info': None, 'cancelled_by': None, 'cancelled_date': None}
    
    try:
        raw_text = await card.text_content() or ''
        if 'cancelled' in raw_text.lower():
            status_data['status'] = 'CANCELLED'
            cancel_text = await get_text(card, CANCELLATION_SELECTOR)
            
            if cancel_text:
                status_data.update(parse_cancellation_from_text(cancel_text))
            else:
                status_data.update(parse_cancellation_from_text(raw_text))
    
    except Exception as e:
        logger.debug(f"Error extracting status info: {e}")
    
    return status_data

# ------------------------------ LICENSE PLATE EXTRACTION ------------------------------

async def extract_license_plate(card: ElementHandle) -> Optional[str]:
    """Extract license plate from a trip card, or None if not found."""
    license_text = await try_selectors(card, LICENSE_PLATE_SELECTORS)
    if license_text:
        normalized = license_text.replace(" ", "").replace("-", "").upper()
        if len(normalized) <= 10 and normalized.isalnum():
            return normalized
    return None

async def extract_trip_id_and_url(card: ElementHandle) -> Dict[str, Optional[str]]:
    """Extract trip ID and URL from a trip card."""
    try:
        href = await card.get_attribute('href')
        if href:
            return {'trip_id': href.split('/')[-1], 'trip_url': href}
    except Exception as e:
        logger.debug(f"Error extracting trip ID: {e}")
    return {'trip_id': None, 'trip_url': None}

# ------------------------------ COMPREHENSIVE EXTRACTION ------------------------------

async def extract_complete_trip_data(card: ElementHandle, card_index: int) -> Dict[str, Any]:
    """Extract all available data from a trip card using parallel processing."""
    try:
        trip_id_data, customer_name, trip_status = await asyncio.gather(
            extract_trip_id_and_url(card),
            extract_customer_name(card, card_index),
            extract_trip_status(card)
        )
        
        trip_dates, vehicle_info, license_plate = await asyncio.gather(
            try_selectors(card, TRIP_DATE_SELECTORS, contains_month_name),
            try_selectors(card, VEHICLE_SELECTORS, contains_vehicle_brand),
            extract_license_plate(card)
        )
        
        trip_data = {'card_index': card_index}
        trip_data.update(trip_id_data)
        trip_data['customer_name'] = customer_name
        trip_data.update(trip_status)
        trip_data.update({
            'trip_dates': trip_dates,
            'vehicle': vehicle_info,
            'license_plate': license_plate
        })
        
        return trip_data

    except Exception as e:
        logger.error(f"Error extracting trip data for card {card_index}: {e}")
        return {'card_index': card_index, 'error': str(e)}

# ------------------------------ MONTH HEADERS EXTRACTION ------------------------------

async def extract_month_headers(page) -> list:
    """Extract month headers from the page."""
    try:
        year_pattern = re.compile(r"\b20\d{2}\b")
        months: list[str] = []

        for selector in MONTH_HEADER_SELECTORS:
            results = await extract_texts_from_elements(
                page,
                selector,
                filter_func=lambda t, pattern=year_pattern: bool(pattern.search(t or ""))
            )
            if results:
                months.extend(results)
                break

        return months

    except Exception as e:
        logger.warning(f"Error extracting month headers: {e}")
        return []

# ------------------------------ VEHICLE EXTRACTION ------------------------------

async def extract_vehicle_status(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract vehicle status from a vehicle card, or None if not found."""
    try:
        status_text = await try_selectors(card, VEHICLE_STATUS_SELECTORS)
        if status_text:
            for status in VEHICLE_STATUSES:
                if status in status_text:
                    return status
        
        raw_text = await card.text_content()
        if raw_text:
            for status in VEHICLE_STATUSES:
                if status in raw_text:
                    return status
        return None
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle status on card {card_index}: {e}")
        return None

async def extract_vehicle_name(card: ElementHandle, card_index: int) -> Dict[str, Optional[str]]:
    """Extract vehicle name and year from a vehicle card."""
    try:
        text_to_parse = await try_selectors(card, VEHICLE_NAME_SELECTORS) or await card.text_content()
        if not text_to_parse:
            return {'name': None, 'year': None}
        
        for line in text_to_parse.split('\n'):
            line = line.strip()
            if not any(year in line for year in VALID_YEARS) or not any(brand in line for brand in VEHICLE_BRANDS):
                continue
            
            cleaned = line
            for prefix in VEHICLE_STATUSES:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
                    if len(cleaned.split()) == 1 and len(cleaned) > 1:
                        for i, char in enumerate(cleaned[1:], 1):
                            if char.islower():
                                cleaned = cleaned[:i] + ' ' + cleaned[i:]
                                break
                    break
            
            year_pattern = YEAR_PATTERN_NON_CAPTURING
            patterns = [
                r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(' + year_pattern + r')',
                r'([A-Za-z]+)\s+([A-Za-z0-9]+).*?(' + year_pattern + r')',
                r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(' + year_pattern + r')[0-9]*\.?[0-9]*[A-Za-z]*'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, cleaned)
                if match:
                    make, model, year = match.groups()
                    return {'name': f"{make} {model}", 'year': year}
            
            year_match = re.search(YEAR_PATTERN_REGEX, cleaned)
            if year_match:
                year = year_match.group(1)
                name = re.sub(YEAR_PATTERN_REGEX, '', cleaned).strip()
                if name:
                    return {'name': name, 'year': year}
            
            patterns_to_remove = [
                r' • [A-Z0-9]+.*', r'No trips.*', r'Vehicle actions.*',
                r'Last trip:.*', r'No ratings.*', r'\([0-9]+ trips?\).*', r'[0-9]+\.[0-9]+.*'
            ]
            for pattern in patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned).strip()
            
            if len(cleaned.split()) >= 2:
                year_match = re.search(YEAR_PATTERN_REGEX, cleaned)
                if year_match:
                    year = year_match.group(1)
                    name = re.sub(YEAR_PATTERN_REGEX, '', cleaned).strip()
                    return {'name': name, 'year': year}
                return {'name': cleaned, 'year': None}
        
        return {'name': None, 'year': None}
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle name on card {card_index}: {e}")
        return {'name': None, 'year': None}

async def extract_vehicle_details(card: ElementHandle, card_index: int) -> Dict[str, Optional[str]]:
    """Extract vehicle details (trim, license plate) from a vehicle card."""
    try:
        elements = await card.query_selector_all(VEHICLE_DETAILS_SELECTORS[0])
        details = {'trim': None, 'license_plate': None}
        
        for element in elements:
            text = await safe_text(element)
            if text:
                cleaned_text = text.replace('•', '').replace(' ', '').replace('-', '').strip()
                
                if any(char.isdigit() for char in cleaned_text) and any(char.isalpha() for char in cleaned_text) and 3 <= len(cleaned_text) <= 10:
                    details['license_plate'] = cleaned_text.upper()
                else:
                    details['trim'] = text.strip()
        return details
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle details on card {card_index}: {e}")
        return {'trim': None, 'license_plate': None}

async def extract_vehicle_trip_info(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract trip information from a vehicle card, or None if not found."""
    return await try_selectors(card, VEHICLE_TRIP_INFO_SELECTORS)

async def extract_vehicle_ratings(card: ElementHandle, card_index: int) -> Dict[str, Optional[float]]:
    """Extract ratings and trip count from a vehicle card."""
    try:
        rating_text = await try_selectors(card, VEHICLE_RATINGS_SELECTORS) or await card.text_content()
        if not rating_text:
            return {'rating': None, 'trip_count': None}
        
        rating_match = extract_with_regex(rating_text, r'(\d+\.?\d*)')
        rating = float(rating_match) if rating_match and 1.0 <= float(rating_match) <= 5.0 else None
        
        trip_match = extract_with_regex(rating_text, r'(\d+)\s*trips?')
        trip_count = int(trip_match) if trip_match else None
        
        return {'rating': rating, 'trip_count': trip_count}
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle ratings on card {card_index}: {e}")
        return {'rating': None, 'trip_count': None}

async def extract_complete_vehicle_data(card: ElementHandle, card_index: int) -> Dict[str, Any]:
    """Extract complete vehicle data from a vehicle card using parallel processing."""
    try:
        status, name_data, details, trip_info, ratings = await asyncio.gather(
            extract_vehicle_status(card, card_index),
            extract_vehicle_name(card, card_index),
            extract_vehicle_details(card, card_index),
            extract_vehicle_trip_info(card, card_index),
            extract_vehicle_ratings(card, card_index)
        )
        
        return {
            'status': status,
            'name': name_data.get('name'),
            'year': name_data.get('year'),
            'trim': details.get('trim'),
            'license_plate': details.get('license_plate'),
            'trip_info': trip_info,
            'rating': ratings.get('rating'),
            'trip_count': ratings.get('trip_count')
        }
    
    except Exception as e:
        logger.warning(f"Error extracting vehicle data for card {card_index}: {e}")
        return {
            'status': None, 'name': None, 'year': None, 'trim': None,
            'license_plate': None, 'trip_info': None, 'rating': None,
            'trip_count': None
        }

# ------------------------------ TRIP DETAIL PAGE EXTRACTION ------------------------------

async def extract_trip_schedule(page: Page) -> Dict[str, Optional[str]]:
    """Extract schedule information (start/end dates and times) from trip detail page."""
    schedule_data = {
        'start_date': None,
        'start_time': None,
        'end_date': None,
        'end_time': None
    }
    
    try:
        date_elements = await page.query_selector_all(SCHEDULE_DATE_SELECTOR)
        if len(date_elements) >= 2:
            schedule_data['start_date'] = await safe_text(date_elements[0])
            schedule_data['end_date'] = await safe_text(date_elements[1])
        
        start_time_element = await page.query_selector(SCHEDULE_TIME_START_SELECTOR)
        if start_time_element:
            schedule_data['start_time'] = await safe_text(start_time_element)
        
        end_time_element = await page.query_selector(SCHEDULE_TIME_END_SELECTOR)
        if end_time_element:
            schedule_data['end_time'] = await safe_text(end_time_element)
            
    except Exception as e:
        logger.debug(f"Error extracting schedule: {e}")
    
    return schedule_data

async def extract_trip_location(page: Page) -> Dict[str, Optional[str]]:
    """Extract location information from trip detail page."""
    location_data = {
        'location_type': None,  
        'address': None
    }
    
    try:
        labels = await extract_texts_from_elements(page, LOCATION_SECTION_LABEL_SELECTOR)
        for label in labels:
            if 'Location' in label or 'Delivery' in label:
                location_data['location_type'] = label.strip()
                break
        
        address_element = await page.query_selector(LOCATION_ADDRESS_SELECTOR)
        if address_element:
            location_data['address'] = await safe_text(address_element)
            
    except Exception as e:
        logger.debug(f"Error extracting location: {e}")
    
    return location_data

async def extract_trip_kilometers(page: Page) -> Dict[str, Optional[Any]]:
    """Extract kilometers information from trip detail page."""
    km_data = {
        'kilometers_included': None,
        'kilometers_driven': None,
        'overage_rate': None
    }
    
    try:
        sections = await page.query_selector_all('.detailsSection')
        
        for section in sections:
            label_element = await section.query_selector(LOCATION_SECTION_LABEL_SELECTOR)
            if not label_element:
                continue
            
            label_text = await safe_text(label_element)
            if not label_text:
                continue
            
            if 'Total Kilometers Included' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText')
                if value_element:
                    value_text = await safe_text(value_element)
                    if value_text:
                        km_match = extract_with_regex(value_text, r'([\d,]+)')
                        if km_match:
                            km_data['kilometers_included'] = int(km_match.replace(',', ''))
                
                overage_element = await section.query_selector(KILOMETERS_OVERAGE_SELECTOR)
                if overage_element:
                    overage_text = await safe_text(overage_element)
                    if overage_text:
                        rate_match = extract_with_regex(overage_text, r'\$([\d.]+)')
                        if rate_match:
                            km_data['overage_rate'] = float(rate_match)
            
            elif 'Kilometers driven' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText')
                if value_element:
                    value_text = await safe_text(value_element)
                    if value_text:
                        km_match = extract_with_regex(value_text, r'([\d,]+)')
                        if km_match:
                            km_data['kilometers_driven'] = int(km_match.replace(',', ''))
                    
    except Exception as e:
        logger.debug(f"Error extracting kilometers: {e}")
    
    return km_data

async def extract_trip_earnings(page: Page) -> Dict[str, Optional[Any]]:
    """Extract earnings information from trip detail page."""
    earnings_data = {
        'total_earnings': None
    }
    
    try:
        sections = await page.query_selector_all('.detailsSection')
        
        for section in sections:
            label_element = await section.query_selector(LOCATION_SECTION_LABEL_SELECTOR)
            if not label_element:
                continue
            
            label_text = await safe_text(label_element)
            if not label_text:
                continue
            
            if 'Total Earnings' in label_text or 'Earnings' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText span')
                if not value_element:
                    value_element = await section.query_selector('.css-14bos0l-StyledText')
                
                if value_element:
                    amount_text = await safe_text(value_element)
                    if amount_text:
                        earnings_data['total_earnings'] = parse_amount(amount_text)
                
                break
                    
    except Exception as e:
        logger.debug(f"Error extracting earnings: {e}")
    
    return earnings_data

async def extract_trip_protection(page: Page) -> Dict[str, Optional[str]]:
    """Extract protection plan information from trip detail page."""
    protection_data = {
        'protection_plan': None,
        'deductible': None
    }
    
    try:
        plan_element = await page.query_selector(PROTECTION_PLAN_SELECTOR)
        if plan_element:
            protection_data['protection_plan'] = await safe_text(plan_element)
        
        deductible_element = await page.query_selector(PROTECTION_DEDUCTIBLE_SELECTOR)
        if deductible_element:
            deductible_text = await safe_text(deductible_element)
            if deductible_text:
                deductible_match = extract_with_regex(deductible_text, r'\$([\d,]+)')
                if deductible_match:
                    protection_data['deductible'] = f"${deductible_match}"
                else:
                    protection_data['deductible'] = deductible_text.strip()
                    
    except Exception as e:
        logger.debug(f"Error extracting protection: {e}")
    
    return protection_data

async def extract_trip_metadata(page: Page) -> Dict[str, Optional[str]]:
    """Extract metadata from trip detail page."""
    return {}

async def extract_complete_trip_detail_data(page: Page, trip_url: str) -> Dict[str, Any]:
    """Extract all detailed trip data from a trip detail page."""
    empty_data = {
        'schedule': {},
        'location': {},
        'kilometers': {},
        'earnings': {},
        'protection': {},
        'metadata': {}
    }
    
    try:
        await page.goto(trip_url, wait_until="domcontentloaded", timeout=TIMEOUT_PAGE_LOAD)
        await page.wait_for_selector(TRIP_DETAILS_CONTAINER, timeout=TIMEOUT_SELECTOR_WAIT)
        
        results = await asyncio.gather(
            extract_trip_schedule(page),
            extract_trip_location(page),
            extract_trip_kilometers(page),
            extract_trip_earnings(page),
            extract_trip_protection(page),
            extract_trip_metadata(page),
            return_exceptions=True
        )
        
        schedule, location, kilometers, earnings, protection, metadata = [
            result if not isinstance(result, Exception) else {}
            for result in results
        ]
        
        return {
            'trip_url': trip_url,
            'schedule': schedule,
            'location': location,
            'kilometers': kilometers,
            'earnings': earnings,
            'protection': protection,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error extracting trip detail data from {trip_url}: {e}")
        return {
            'trip_url': trip_url,
            'error': str(e),
            **empty_data
        }
