# ------------------------------ IMPORTS ------------------------------
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import ElementHandle

from core.utils.logger import logger
from core.utils.browser_helpers import safe_text
from .selectors import (
    TRIP_DATE_SELECTORS, VEHICLE_SELECTORS, CUSTOMER_SELECTORS,
    CANCELLATION_SELECTOR, LICENSE_PLATE_SELECTORS, ALL_IMAGES,
    MONTH_HEADER_SELECTORS, is_vehicle_related, is_customer_related,
    contains_month_name, contains_vehicle_brand,
    VEHICLE_STATUS_SELECTORS, VEHICLE_IMAGE_SELECTORS, VEHICLE_NAME_SELECTORS,
    VEHICLE_DETAILS_SELECTORS, VEHICLE_TRIP_INFO_SELECTORS, VEHICLE_RATINGS_SELECTORS
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def try_selectors(card: ElementHandle, selectors: List[str], validator=None) -> Optional[str]:
    """Try multiple selectors and return first valid result."""
    for selector in selectors:
        try:
            text = await safe_text(card, selector)
            if text and (not validator or validator(text)):
                return text.strip()
        except Exception:
            continue
    return None

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    match = re.search(pattern, text)
    return match.group(group) if match else None

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
    """Parse cancellation information from raw text."""
    cancellation_data = {
        'cancellation_info': None,
        'cancelled_by': None,
        'cancelled_date': None
    }
    
    if 'cancelled' not in raw_text.lower():
        return cancellation_data
    
    lines = raw_text.split('\n')
    for line in lines:
        if 'cancelled' in line.lower():
            cancellation_data['cancellation_info'] = line.strip()
            if ' cancelled on ' in line:
                parts = line.split(' cancelled on ')
                cancellation_data['cancelled_by'] = parts[0].strip()
                cancellation_data['cancelled_date'] = parts[1].strip()
            break
    
    return cancellation_data

# ------------------------------ CUSTOMER EXTRACTION ------------------------------

async def extract_customer_info(card: ElementHandle, card_index: int) -> Dict[str, Any]:
    """Extract customer information from a trip card."""
    customer_text = await try_selectors(card, CUSTOMER_SELECTORS, lambda t: '#' in t)
    
    if not customer_text:
        try:
            raw_text = await card.text_content() or ''
            for line in raw_text.split('\n'):
                if '#' in line and any(char.isalpha() for char in line):
                    customer_text = line.strip()
                    break

        except Exception as e:
            logger.debug(f"Error extracting customer info on card {card_index}: {e}")
    
    if customer_text:
        return {
            'customer_info': customer_text,
            'customer_name': customer_text.split('#')[0].strip(),
            'customer_found': True
        }
    
    return {'customer_info': None, 'customer_name': None, 'customer_found': False}

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
            cancel_text = await safe_text(card, CANCELLATION_SELECTOR)
            if cancel_text:
                status_data['cancellation_info'] = cancel_text
                if ' cancelled on ' in cancel_text:
                    parts = cancel_text.split(' cancelled on ')
                    status_data['cancelled_by'] = parts[0].strip()
                    status_data['cancelled_date'] = parts[1].strip()
            else:
                status_data.update(parse_cancellation_from_text(raw_text))
    
    except Exception as e:
        logger.debug(f"Error extracting status info: {e}")
    
    return status_data

# ------------------------------ IMAGE EXTRACTION ------------------------------

async def extract_trip_images(card: ElementHandle) -> Dict[str, list]:
    """Extract all images from a trip card and classify them."""
    images_data = {'vehicle_images': [], 'customer_images': [], 'other_images': []}
    
    try:
        for img in await card.query_selector_all(ALL_IMAGES):
            try:
                src = await img.get_attribute('src')
                if not src:
                    continue
                
                alt = await img.get_attribute('alt') or ""
                data_testid = await img.get_attribute('data-testid') or ""
                image_info = {'url': src, 'alt': alt, 'data_testid': data_testid}
                
                if is_vehicle_related(alt, src):
                    image_info['type'] = 'vehicle'
                    images_data['vehicle_images'].append(image_info)
                elif is_customer_related(data_testid, src):
                    image_info['type'] = 'customer'
                    images_data['customer_images'].append(image_info)
                else:
                    image_info['type'] = 'unknown'
                    images_data['other_images'].append(image_info)
            
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Error extracting images: {e}")
    
    return images_data

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
    """Extract all available data from a trip card."""
    try:
        raw_text = await card.text_content() or ''
        trip_data = {'card_index': card_index, 'raw_card_text': raw_text.strip()}
        
        trip_data.update(await extract_trip_id_and_url(card))
        trip_data.update(await extract_customer_info(card, card_index))
        trip_data.update(await extract_trip_status(card))
        trip_data.update(await extract_trip_images(card))
        
        trip_data.update({
            'trip_dates': await extract_trip_dates(card),
            'vehicle': await extract_vehicle_info(card),
            'license_plate': await extract_license_plate(card)
        })
        
        if trip_data['vehicle_images']:
            trip_data['vehicle_image'] = trip_data['vehicle_images'][0]['url']
        if trip_data['customer_images']:
            trip_data['customer_profile_image'] = trip_data['customer_images'][0]['url']
        trip_data['has_customer_photo'] = len(trip_data['customer_images']) > 0
        
        return trip_data
    except Exception as e:
        logger.error(f"Error extracting trip data for card {card_index}: {e}")
        return {'card_index': card_index, 'error': str(e)}

# ------------------------------ MONTH HEADERS EXTRACTION ------------------------------

async def extract_month_headers(page) -> list:
    """Extract month headers from the page."""
    try:
        headers = await page.query_selector_all(MONTH_HEADER_SELECTORS[0])
        return [await safe_text(header) for header in headers 
                if await safe_text(header) and ('2024' in await safe_text(header) or '2025' in await safe_text(header))]
    except Exception as e:
        logger.warning(f"Error extracting month headers: {e}")
        return []

# ------------------------------ VEHICLE EXTRACTION ------------------------------

async def extract_vehicle_status(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract vehicle status from a vehicle card, or None if not found."""
    try:
        status_text = await try_selectors(card, VEHICLE_STATUS_SELECTORS)
        if status_text:
            for status in ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']:
                if status in status_text:
                    return status
        
        raw_text = await card.text_content()
        if raw_text:
            for status in ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']:
                if status in raw_text:
                    return status
        return None
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle status on card {card_index}: {e}")
        return None

async def extract_vehicle_image(card: ElementHandle, card_index: int) -> Dict[str, Optional[str]]:
    """Extract vehicle image information from a vehicle card."""
    for selector in VEHICLE_IMAGE_SELECTORS:
        try:
            img_element = await card.query_selector(selector)
            if img_element:
                return {
                    'url': await img_element.get_attribute('src'),
                    'alt': await img_element.get_attribute('alt'),
                    'srcset': await img_element.get_attribute('srcset')
                }
        
        except Exception:
            continue
    return {'url': None, 'alt': None, 'srcset': None}

async def extract_vehicle_name(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract vehicle name from a vehicle card, or None if not found."""
    try:
        text_to_parse = await try_selectors(card, VEHICLE_NAME_SELECTORS) or await card.text_content()
        if not text_to_parse:
            return None
        
        for line in text_to_parse.split('\n'):
            line = line.strip()
            if any(year in line for year in ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']):
                if any(brand in line for brand in ['Audi', 'Hyundai', 'Toyota', 'Honda', 'BMW', 'Mercedes', 'Ford', 'Chevrolet']):
                    cleaned = line
                    for prefix in ['Snoozed', 'Listed', 'Unavailable', 'Maintenance']:
                        if cleaned.startswith(prefix):
                            cleaned = cleaned[len(prefix):].strip()
                            if len(cleaned.split()) == 1 and len(cleaned) > 1:
                                for i, char in enumerate(cleaned[1:], 1):
                                    if char.islower():
                                        cleaned = cleaned[:i] + ' ' + cleaned[i:]
                                        break
                            break
                    
                    patterns = [
                        r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(201[7-9]|202[0-5])',
                        r'([A-Za-z]+)\s+([A-Za-z0-9]+).*?(201[7-9]|202[0-5])',
                        r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(201[7-9]|202[0-5])[0-9]*\.?[0-9]*[A-Za-z]*'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, cleaned)
                        if match:
                            make, model, year = match.groups()
                            return f"{make} {model} {year}"
                    
                    cleaned = clean_text(cleaned)
                    if len(cleaned.split()) >= 2:
                        return cleaned
        return None
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle name on card {card_index}: {e}")
        return None

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
    """Extract complete vehicle data from a vehicle card."""
    try:
        vehicle_id = None
        try:
            link_element = await card.query_selector('a[href*="/your-car/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                vehicle_id = extract_with_regex(href or '', r'/your-car/(\d+)') if href else None
        
        except Exception:
            pass
        
        status = await extract_vehicle_status(card, card_index)
        image_data = await extract_vehicle_image(card, card_index)
        name = await extract_vehicle_name(card, card_index)
        details = await extract_vehicle_details(card, card_index)
        trip_info = await extract_vehicle_trip_info(card, card_index)
        ratings = await extract_vehicle_ratings(card, card_index)
        
        return {
            'vehicle_id': vehicle_id,
            'status': status,
            'name': name,
            'trim': details.get('trim'),
            'license_plate': details.get('license_plate'),
            'trip_info': trip_info,
            'rating': ratings.get('rating'),
            'trip_count': ratings.get('trip_count'),
            'image': image_data
        }
    
    except Exception as e:
        logger.warning(f"Error extracting vehicle data for card {card_index}: {e}")
        return {
            'vehicle_id': None, 'status': None, 'name': None, 'trim': None,
            'license_plate': None, 'trip_info': None, 'rating': None,
            'trip_count': None, 'image': {'url': None, 'alt': None, 'srcset': None}
        }
