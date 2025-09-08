# ------------------------------ IMPORTS ------------------------------
from playwright.async_api import ElementHandle

from utils.logger import logger
from .selectors import (
    TRIP_DATE_SELECTORS, VEHICLE_SELECTORS, CUSTOMER_SELECTORS,
    CANCELLATION_SELECTOR, LICENSE_PLATE_SELECTORS, ALL_IMAGES,
    MONTH_HEADER, is_vehicle_related, is_customer_related,
    contains_month_name, contains_vehicle_brand
)

# ------------------------------ CUSTOMER EXTRACTION ------------------------------

async def extract_customer_info(card: ElementHandle, card_index: int):
    """
    Extract customer information from a trip card.
    
    Args:
        card: The trip card element
        card_index: Index of the card for logging
        
    Returns:
        Dict containing customer_info, customer_name, and customer_found flag
    """
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
                try:
                    text = await element.text_content()
                    if text and '#' in text:
                        customer_data['customer_info'] = text.strip()
                        customer_data['customer_name'] = text.split('#')[0].strip()
                        customer_data['customer_found'] = True
                        break
                except:
                    continue
        except:
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
        except:
            pass
    
    return customer_data

# ------------------------------ DATE EXTRACTION ------------------------------

async def extract_trip_dates(card: ElementHandle):
    """
    Extract trip dates from a trip card.
    
    Args:
        card: The trip card element
        
    Returns:
        Trip dates string or None if not found
    """
    for selector in TRIP_DATE_SELECTORS:
        try:
            date_element = await card.query_selector(selector)
            if date_element:
                date_text = await date_element.text_content()
                if date_text and contains_month_name(date_text):
                    return date_text.strip()
        except:
            continue
    
    return None

# ------------------------------ VEHICLE EXTRACTION ------------------------------

async def extract_vehicle_info(card: ElementHandle):
    """
    Extract vehicle information from a trip card.
    
    Args:
        card: The trip card element
        
    Returns:
        Vehicle info string or None if not found
    """
    for selector in VEHICLE_SELECTORS:
        try:
            vehicle_element = await card.query_selector(selector)
            if vehicle_element:
                vehicle_text = await vehicle_element.text_content()
                if vehicle_text and contains_vehicle_brand(vehicle_text):
                    return vehicle_text.strip()
        except:
            continue
    
    return None

# ------------------------------ STATUS EXTRACTION ------------------------------

async def extract_trip_status(card: ElementHandle):
    """
    Extract trip status and cancellation information.
    
    Args:
        card: The trip card element
        
    Returns:
        Dict containing status, cancellation_info, cancelled_by, cancelled_date
    """
    status_data = {
        'status': 'completed',
        'cancellation_info': None,
        'cancelled_by': None,
        'cancelled_date': None
    }
    
    try:
        raw_text = await card.text_content() or ''
        
        if 'cancelled' in raw_text.lower():
            status_data['status'] = 'cancelled'
            
            try:
                cancel_element = await card.query_selector(CANCELLATION_SELECTOR)
                if cancel_element:
                    cancel_text = await cancel_element.text_content()
                    if cancel_text:
                        status_data['cancellation_info'] = cancel_text.strip()
                        
                        if ' cancelled on ' in cancel_text:
                            parts = cancel_text.split(' cancelled on ')
                            status_data['cancelled_by'] = parts[0].strip()
                            status_data['cancelled_date'] = parts[1].strip()
            except:
                pass
            
            if not status_data['cancellation_info']:
                lines = raw_text.split('\n')
                for line in lines:
                    if 'cancelled' in line.lower():
                        status_data['cancellation_info'] = line.strip()
                        if ' cancelled on ' in line:
                            parts = line.split(' cancelled on ')
                            status_data['cancelled_by'] = parts[0].strip()
                            status_data['cancelled_date'] = parts[1].strip()
                        break
    except:
        pass
    
    return status_data

# ------------------------------ IMAGE EXTRACTION ------------------------------

async def extract_trip_images(card: ElementHandle):
    """
    Extract all images from a trip card and classify them.
    
    Args:
        card: The trip card element
        
    Returns:
        Dict containing vehicle_images, customer_images, and other_images lists
    """
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
                    
            except:
                continue
                
    except:
        pass
    
    return images_data

# ------------------------------ LICENSE PLATE EXTRACTION ------------------------------

async def extract_license_plate(card: ElementHandle):
    """
    Extract license plate from a trip card.
    
    Args:
        card: The trip card element
        
    Returns:
        License plate string or None if not found
    """
    for selector in LICENSE_PLATE_SELECTORS:
        try:
            license_element = await card.query_selector(selector)
            if license_element:
                license_text = await license_element.text_content()
                if (license_text and 
                    len(license_text.strip()) <= 10 and 
                    license_text.strip().isupper()):
                    return license_text.strip()
        except:
            continue
    
    return None

# ------------------------------ TRIP ID EXTRACTION ------------------------------

async def extract_trip_id_and_url(card: ElementHandle):
    """
    Extract trip ID and URL from a trip card.
    
    Args:
        card: The trip card element
        
    Returns:
        Dict containing trip_id and trip_url
    """
    try:
        href = await card.get_attribute('href')
        if href:
            trip_id = href.split('/')[-1]
            return {
                'trip_id': trip_id,
                'trip_url': href
            }
    except:
        pass
    
    return {
        'trip_id': None,
        'trip_url': None
    }

# ------------------------------ COMPREHENSIVE EXTRACTION ------------------------------

async def extract_complete_trip_data(card: ElementHandle, card_index: int):
    """
    Extract all available data from a trip card.
    
    Args:
        card: The trip card element
        card_index: Index of the card for logging
        
    Returns:
        Complete trip data dictionary
    """
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

async def extract_month_headers(page):
    """
    Extract month headers from the page.
    
    Args:
        page: Playwright page object
        
    Returns:
        List of month headers
    """
    months_list = []
    
    try:
        month_headers = await page.query_selector_all(MONTH_HEADER)
        
        for header in month_headers:
            try:
                month_text = await header.text_content()
                if month_text and ('2024' in month_text or '2025' in month_text):
                    months_list.append(month_text)
            except:
                continue
                
    except Exception as e:
        logger.warning(f"Error extracting month headers: {e}")
    
    return months_list
