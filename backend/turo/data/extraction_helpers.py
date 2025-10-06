# ------------------------------ IMPORTS ------------------------------
import re
from typing import Optional, Dict, Any
from playwright.async_api import ElementHandle

from core.utils.logger import logger
from .selectors import (
    TRIP_DATE_SELECTORS, VEHICLE_SELECTORS, CUSTOMER_SELECTORS,
    CANCELLATION_SELECTOR, LICENSE_PLATE_SELECTORS, ALL_IMAGES,
    MONTH_HEADER_SELECTORS, is_vehicle_related, is_customer_related,
    contains_month_name, contains_vehicle_brand,
    VEHICLE_STATUS_SELECTORS, VEHICLE_IMAGE_SELECTORS, VEHICLE_NAME_SELECTORS,
    VEHICLE_DETAILS_SELECTORS, VEHICLE_TRIP_INFO_SELECTORS, VEHICLE_RATINGS_SELECTORS
)

# ------------------------------ HELPER FUNCTIONS ------------------------------

from core.utils.browser_helpers import safe_text

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

async def extract_customer_info(card: ElementHandle, card_index: int):
    """Extract customer information from a trip card."""
    customer_data = {
        'customer_info': None,
        'customer_name': None,
        'customer_found': False
    }
    
    for selector in CUSTOMER_SELECTORS:
        if customer_data['customer_found']:
            break
            
        try:
            customer_elements = await card.query_selector_all(selector)
            for element in customer_elements:
                text = await safe_text(element)
                if text and '#' in text:
                    customer_data['customer_info'] = text
                    customer_data['customer_name'] = text.split('#')[0].strip()
                    customer_data['customer_found'] = True
                    break
        
        except Exception as e:
            logger.debug(f"Error extracting customer info with selectors on card {card_index}: {e}")
            continue
    
    if not customer_data['customer_found']:
        try:
            raw_text = await card.text_content() or ''
            lines = raw_text.split('\n')
            
            for line in lines:
                if '#' in line and any(char.isalpha() for char in line):
                    customer_data['customer_info'] = line.strip()
                    customer_data['customer_name'] = line.split('#')[0].strip()
                    customer_data['customer_found'] = True
                    break
        
        except Exception as e:
            logger.debug(f"Error extracting customer info from raw text on card {card_index}: {e}")
    
    return customer_data

# ------------------------------ DATE EXTRACTION ------------------------------

async def extract_trip_dates(card: ElementHandle) -> Optional[str]:
    """Extract trip dates string from a trip card, or None if not found."""
    for selector in TRIP_DATE_SELECTORS:
        date_text = await safe_text(card, selector)
        if date_text and contains_month_name(date_text):
            return date_text
    
    return None

# ------------------------------ VEHICLE EXTRACTION ------------------------------

async def extract_vehicle_info(card: ElementHandle) -> Optional[str]:
    """Extract vehicle info string from a trip card, or None if not found."""
    for selector in VEHICLE_SELECTORS:
        vehicle_text = await safe_text(card, selector)
        if vehicle_text and contains_vehicle_brand(vehicle_text):
            return vehicle_text
    
    return None

# ------------------------------ STATUS EXTRACTION ------------------------------

async def extract_trip_status(card: ElementHandle) -> Dict[str, Any]:
    """Extract trip status and cancellation information."""
    status_data = {
        'status': 'COMPLETED',
        'cancellation_info': None,
        'cancelled_by': None,
        'cancelled_date': None
    }
    
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
            
            if not status_data['cancellation_info']:
                cancellation_data = parse_cancellation_from_text(raw_text)
                status_data.update(cancellation_data)

    except Exception as e:
        logger.debug(f"Error extracting status info from raw text: {e}")
    
    return status_data

# ------------------------------ IMAGE EXTRACTION ------------------------------

async def extract_trip_images(card: ElementHandle) -> Dict[str, list]:
    """Extract all images from a trip card and classify them."""
    images_data = {
        'vehicle_images': [],
        'customer_images': [],
        'other_images': []
    }
    
    try:
        all_images = await card.query_selector_all(ALL_IMAGES)
        
        for img in all_images:
            try:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ""
                data_testid = await img.get_attribute('data-testid') or ""
                
                if not src:
                    continue
                
                image_info = {
                    'url': src,
                    'alt': alt,
                    'data_testid': data_testid
                }
                
                if is_vehicle_related(alt, src):
                    image_info['type'] = 'vehicle'
                    images_data['vehicle_images'].append(image_info)
                elif is_customer_related(data_testid, src):
                    image_info['type'] = 'customer'
                    images_data['customer_images'].append(image_info)
                else:
                    image_info['type'] = 'unknown'
                    images_data['other_images'].append(image_info)
                    
            except Exception as e:
                logger.debug(f"Error processing image: {e}")
                continue
                
    except Exception as e:
        logger.debug(f"Error extracting images: {e}")
    
    return images_data

# ------------------------------ LICENSE PLATE EXTRACTION ------------------------------

async def extract_license_plate(card: ElementHandle) -> Optional[str]:
    """Extract license plate from a trip card, or None if not found."""
    for selector in LICENSE_PLATE_SELECTORS:
        license_text = await safe_text(card, selector)

        if license_text:
            normalized = license_text.replace(" ", "").replace("-", "").upper()
            if len(normalized) <= 10 and normalized.isalnum():
                return normalized
    
    return None

# ------------------------------ TRIP ID EXTRACTION ------------------------------

async def extract_trip_id_and_url(card: ElementHandle) -> Dict[str, Optional[str]]:
    """Extract trip ID and URL from a trip card."""
    try:
        href = await card.get_attribute('href')
        if href:
            trip_id = href.split('/')[-1]
            return {
                'trip_id': trip_id,
                'trip_url': href
            }
    
    except Exception as e:
        logger.debug(f"Error extracting trip ID from href: {e}")
    
    return {
        'trip_id': None,
        'trip_url': None
    }

# ------------------------------ COMPREHENSIVE EXTRACTION ------------------------------

async def extract_complete_trip_data(card: ElementHandle, card_index: int) -> Dict[str, Any]:
    """Extract all available data from a trip card."""
    try:
        raw_text = await card.text_content() or ''
        
        trip_data = {
            'card_index': card_index,
            'raw_card_text': raw_text.strip()
        }
        
        id_data = await extract_trip_id_and_url(card)
        trip_data.update(id_data)
        
        trip_data['trip_dates'] = await extract_trip_dates(card)
        trip_data['vehicle'] = await extract_vehicle_info(card)
        trip_data['license_plate'] = await extract_license_plate(card)
        
        customer_data = await extract_customer_info(card, card_index)
        trip_data.update(customer_data)
        
        status_data = await extract_trip_status(card)
        trip_data.update(status_data)
        
        images_data = await extract_trip_images(card)
        trip_data.update(images_data)
        
        if trip_data['vehicle_images']:
            trip_data['vehicle_image'] = trip_data['vehicle_images'][0]['url']
        
        if trip_data['customer_images']:
            trip_data['customer_profile_image'] = trip_data['customer_images'][0]['url']
        
        trip_data['has_customer_photo'] = len(trip_data['customer_images']) > 0
        
        return trip_data
        
    except Exception as e:
        logger.error(f"Error extracting complete trip data for card {card_index}: {e}")
        return {
            'card_index': card_index,
            'error': str(e)
        }

# ------------------------------ MONTH HEADERS EXTRACTION ------------------------------

async def extract_month_headers(page) -> list:
    """Extract month headers from the page."""
    months_list = []
    
    try:
        month_headers = await page.query_selector_all(MONTH_HEADER_SELECTORS[0])
        
        for header in month_headers:
            month_text = await safe_text(header)
            if month_text and ('2024' in month_text or '2025' in month_text):
                months_list.append(month_text)
                
    except Exception as e:
        logger.warning(f"Error extracting month headers: {e}")
    
    return months_list

# ------------------------------ VEHICLE EXTRACTION ------------------------------

async def extract_vehicle_status(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract vehicle status from a vehicle card, or None if not found."""
    try:
        for selector in VEHICLE_STATUS_SELECTORS:
            status_text = await safe_text(card, selector)
            if status_text and status_text.strip():
                cleaned = status_text.strip()
                if cleaned in ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']:
                    return cleaned
                for status in ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']:
                    if status in cleaned:
                        return status
        
        raw_text = await card.text_content()
        if raw_text:
            raw_text = raw_text.strip()
            for status in ['Listed', 'Snoozed', 'Unavailable', 'Maintenance']:
                if status in raw_text:
                    return status
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting vehicle status on card {card_index}: {e}")
        return None

async def extract_vehicle_image(card: ElementHandle, card_index: int) -> Dict[str, Optional[str]]:
    """Extract vehicle image information from a vehicle card."""
    image_data = {
        'url': None,
        'alt': None,
        'srcset': None
    }
    
    for selector in VEHICLE_IMAGE_SELECTORS:
        try:
            img_element = await card.query_selector(selector)
            if img_element:
                image_data['url'] = await img_element.get_attribute('src')
                image_data['alt'] = await img_element.get_attribute('alt')
                image_data['srcset'] = await img_element.get_attribute('srcset')
                break
        
        except Exception as e:
            logger.debug(f"Error extracting vehicle image with selector on card {card_index}: {e}")
            continue
    
    return image_data

async def extract_vehicle_name(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract vehicle name from a vehicle card, or None if not found."""
    try:
        raw_name_text = None
        for selector in VEHICLE_NAME_SELECTORS:
            name_text = await safe_text(card, selector)
            logger.info(f"Vehicle name selector '{selector}' returned: '{name_text}'")
            if name_text and name_text.strip():
                raw_name_text = name_text.strip()
                logger.info(f"Found vehicle name via selector: '{raw_name_text}'")
                break
        
        text_to_parse = raw_name_text if raw_name_text else await card.text_content()
        logger.info(f"Text to parse for card {card_index}: '{text_to_parse}'")
        
        if text_to_parse:
            lines = text_to_parse.split('\n')
            for line in lines:
                line = line.strip()
                # Check if line contains year and vehicle brand
                if any(year in line for year in ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']):
                    if any(brand in line for brand in ['Audi', 'Hyundai', 'Toyota', 'Honda', 'BMW', 'Mercedes', 'Ford', 'Chevrolet']):
                        # Clean up the line more aggressively
                        cleaned = line
                        
                        # Remove status prefixes
                        for prefix in ['Snoozed', 'Listed', 'Unavailable', 'Maintenance']:
                            if cleaned.startswith(prefix):
                                cleaned = cleaned[len(prefix):].strip()
                                # If there's no space after removing prefix, try to separate the words
                                # Only do this if the first word is immediately followed by another word (no space)
                                if cleaned and cleaned[0].isupper():
                                    # Check if we need to separate words (like "SnoozedAudi" -> "Snoozed Audi")
                                    words = cleaned.split()
                                    if len(words) == 1 and len(cleaned) > 1:
                                        # Find the first lowercase letter and insert space before it
                                        for i, char in enumerate(cleaned[1:], 1):
                                            if char.islower():
                                                cleaned = cleaned[:i] + ' ' + cleaned[i:]
                                                break
                                break
                        
                        # Try to extract vehicle info BEFORE removing extra patterns
                        # Look for pattern like "Audi Q7 2017" or "Hyundai Elantra 2017"
                        vehicle_match = re.search(r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(201[7-9]|202[0-5])', cleaned)
                        if vehicle_match:
                            make, model, year = vehicle_match.groups()
                            result = f"{make} {model} {year}"
                            logger.info(f"✅ Successfully parsed vehicle: '{result}'")
                            return result
                        
                        # If that didn't work, try a more flexible approach
                        # Look for make + model + year anywhere in the cleaned text
                        flexible_match = re.search(r'([A-Za-z]+)\s+([A-Za-z0-9]+).*?(201[7-9]|202[0-5])', cleaned)
                        if flexible_match:
                            make, model, year = flexible_match.groups()
                            result = f"{make} {model} {year}"
                            logger.debug(f"✅ Successfully parsed vehicle (flexible): '{result}'")
                            return result
                        
                        # If still no match, try to find year in the original text and reconstruct
                        # Look for patterns like "Audi Q7 20173.0T" where year is embedded
                        year_match = re.search(r'([A-Za-z]+)\s+([A-Za-z0-9]+)\s+(201[7-9]|202[0-5])[0-9]*\.?[0-9]*[A-Za-z]*', cleaned)
                        if year_match:
                            make, model, year = year_match.groups()
                            result = f"{make} {model} {year}"
                            logger.debug(f"✅ Successfully parsed vehicle (embedded year): '{result}'")
                            return result
                        
                        # Only remove extra patterns if we haven't found a match yet
                        extra_patterns = [
                            r' • [A-Z0-9]+.*',  
                            r'No trips.*',       
                            r'Vehicle actions.*', 
                            r'Last trip:.*',     
                            r'No ratings.*',
                            r'\([0-9]+ trips?\).*',
                            r'[0-9]+\.[0-9]+.*',
                        ]
                        for pattern in extra_patterns:
                            cleaned = re.sub(pattern, '', cleaned).strip()
                        
                        if cleaned and len(cleaned.split()) >= 2:
                            return cleaned
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting vehicle name on card {card_index}: {e}")
        return None

async def extract_vehicle_details(card: ElementHandle, card_index: int) -> Dict[str, Optional[str]]:
    """Extract vehicle details (trim, license plate) from a vehicle card."""
    details_data = {
        'trim': None,
        'license_plate': None
    }
    
    try:
        detail_elements = await card.query_selector_all(VEHICLE_DETAILS_SELECTORS[0])
        for element in detail_elements:
            text = await safe_text(element)
            if text:
                if any(char.isdigit() for char in text) and any(char.isalpha() for char in text) and len(text) <= 10:
                    details_data['license_plate'] = text
                else:
                    details_data['trim'] = text
    
    except Exception as e:
        logger.debug(f"Error extracting vehicle details on card {card_index}: {e}")
    
    return details_data

async def extract_vehicle_trip_info(card: ElementHandle, card_index: int) -> Optional[str]:
    """Extract trip information from a vehicle card, or None if not found."""
    for selector in VEHICLE_TRIP_INFO_SELECTORS:
        trip_text = await safe_text(card, selector)
        if trip_text:
            return trip_text
    
    return None

async def extract_vehicle_ratings(card: ElementHandle, card_index: int) -> Dict[str, Optional[float]]:
    """Extract ratings and trip count from a vehicle card."""
    ratings_data = {
        'rating': None,
        'trip_count': None
    }
    
    try:
        for selector in VEHICLE_RATINGS_SELECTORS:
            rating_text = await safe_text(card, selector)
            if rating_text:
                # Look for rating patterns (1-5 range)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating_value = float(rating_match.group(1))
                    # Only accept reasonable rating values (1-5)
                    if 1.0 <= rating_value <= 5.0:
                        ratings_data['rating'] = rating_value
                
                # Look for trip count patterns
                trip_match = re.search(r'(\d+)\s*trips?', rating_text)
                if trip_match:
                    ratings_data['trip_count'] = int(trip_match.group(1))
                
                if ratings_data['rating'] or ratings_data['trip_count']:
                    break
        
        # Fallback: try to extract from raw text
        if not ratings_data['rating'] and not ratings_data['trip_count']:
            raw_text = await card.text_content()
            if raw_text:
                # Look for rating patterns in the entire text
                rating_matches = re.findall(r'(\d+\.?\d*)', raw_text)
                for match in rating_matches:
                    rating_value = float(match)
                    if 1.0 <= rating_value <= 5.0:
                        ratings_data['rating'] = rating_value
                        break
                
                # Look for trip count patterns
                trip_matches = re.findall(r'(\d+)\s*trips?', raw_text)
                if trip_matches:
                    ratings_data['trip_count'] = int(trip_matches[0])
        
        return ratings_data
        
    except Exception as e:
        logger.debug(f"Error extracting vehicle ratings on card {card_index}: {e}")
        return {'rating': None, 'trip_count': None}

async def extract_complete_vehicle_data(card: ElementHandle, card_index: int) -> Dict[str, Any]:
    """Extract complete vehicle data from a vehicle card."""
    try:
        status = await extract_vehicle_status(card, card_index)
        image_data = await extract_vehicle_image(card, card_index)
        name = await extract_vehicle_name(card, card_index)
        details = await extract_vehicle_details(card, card_index)
        trip_info = await extract_vehicle_trip_info(card, card_index)
        ratings = await extract_vehicle_ratings(card, card_index)
        
        vehicle_id = None
        try:
            link_element = await card.query_selector('a[href*="/your-car/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    id_match = re.search(r'/your-car/(\d+)', href)
                    if id_match:
                        vehicle_id = id_match.group(1)
        
        except Exception as e:
            logger.debug(f"Error extracting vehicle ID from href on card {card_index}: {e}")
        
        vehicle_data = {
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
        
        return vehicle_data
        
    except Exception as e:
        logger.warning(f"Error extracting vehicle data for card {card_index}: {e}")
        return {
            'vehicle_id': None,
            'status': None,
            'name': None,
            'trim': None,
            'license_plate': None,
            'trip_info': None,
            'rating': None,
            'trip_count': None,
            'image': {'url': None, 'alt': None, 'srcset': None}
        }
