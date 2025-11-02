# ------------------------------ IMPORTS ------------------------------
import asyncio
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import ElementHandle

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text
from .helpers import extract_with_regex, try_selectors, get_text, extract_texts_from_elements
from .selectors import (
    TRIP_DATE_SELECTORS, VEHICLE_SELECTORS, CUSTOMER_SELECTORS,
    CANCELLATION_SELECTOR, LICENSE_PLATE_SELECTORS,
    MONTH_HEADER_SELECTORS,
    contains_month_name, contains_vehicle_brand,
    VEHICLE_STATUS_SELECTORS, VEHICLE_NAME_SELECTORS,
    VEHICLE_DETAILS_SELECTORS, VEHICLE_TRIP_INFO_SELECTORS, VEHICLE_RATINGS_SELECTORS,
    VALID_YEARS, VEHICLE_BRANDS, MONTH_NAMES, VEHICLE_STATUSES, YEAR_PATTERN_REGEX, YEAR_PATTERN_NON_CAPTURING
)

def clean_text(text: str, patterns_to_remove: List[str] = None) -> str:
    """Clean text by removing unwanted patterns."""
    if not patterns_to_remove:
        patterns_to_remove = [
            r' • [A-Z0-9]+.*', r'No trips.*', r'Vehicle actions.*',
            r'Last trip:.*', r'No ratings.*', r'\([0-9]+ trips?\).*', r'[0-9]+\.[0-9]+.*'
        ]
    
    cleaned = text.strip()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned).strip()
    return cleaned

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
            
            # If cancelled, reuse parse_cancellation_from_text to extract customer name
            if 'cancelled' in raw_text.lower() and ' cancelled on ' in raw_text:
                cancellation_data = parse_cancellation_from_text(raw_text)
                if cancellation_data.get('cancelled_by'):
                    return cancellation_data['cancelled_by']
            
            # Fallback: search for customer name with # pattern
            for line in raw_text.split('\n'):
                if '#' in line and any(char.isalpha() for char in line):
                    customer_text = line.strip()
                    break

        except Exception as e:
            logger.debug(f"Error extracting customer name on card {card_index}: {e}")
    
    if customer_text:
        return customer_text.split('#')[0].strip()
    
    return None

# ------------------------------ DATE EXTRACTION ------------------------------

async def extract_trip_dates(card: ElementHandle) -> Optional[str]:
    """Extract trip dates string from a trip card, or None if not found."""
    return await try_selectors(card, TRIP_DATE_SELECTORS, contains_month_name)

async def extract_vehicle_info(card: ElementHandle) -> Optional[str]:
    """Extract vehicle info string from a trip card, or None if not found."""
    return await try_selectors(card, VEHICLE_SELECTORS, contains_vehicle_brand)

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
            extract_trip_dates(card),
            extract_vehicle_info(card),
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
            if any(year in line for year in VALID_YEARS):
                if any(brand in line for brand in VEHICLE_BRANDS):
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
                            return {
                                'name': f"{make} {model}",
                                'year': year
                            }
                    
                    year_match = re.search(YEAR_PATTERN_REGEX, cleaned)
                    if year_match:
                        year = year_match.group(1)
                        name = re.sub(YEAR_PATTERN_REGEX, '', cleaned).strip()
                        if name:
                            return {'name': name, 'year': year}
                    
                    cleaned = clean_text(cleaned)
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
                if any(char.isdigit() for char in text) and any(char.isalpha() for char in text) and len(text) <= 10:
                    details['license_plate'] = text
                else:
                    details['trim'] = text
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
