# ------------------------------ IMPORTS ------------------------------
import asyncio
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.async_api import ElementHandle, Page
import logging


logger = logging.getLogger(__name__)
from core.config.settings import TIMEOUT_SELECTOR_WAIT, TIMEOUT_PAGE_LOAD
from .helpers import extract_with_regex, try_selectors, get_text, extract_texts_from_elements
from core.utils.route_helpers import parse_amount
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
    PROTECTION_DEDUCTIBLE_SELECTOR, RESERVATION_NUMBER_SELECTOR,
    RECEIPT_HEADER_SELECTOR, RECEIPT_RESERVATION_ID_SELECTOR, RECEIPT_TRIP_DETAILS_SECTION,
    RECEIPT_HOST_NAME_SELECTOR, RECEIPT_VEHICLE_NAME_SELECTOR, RECEIPT_BOOKED_DATE_SELECTOR,
    RECEIPT_GUEST_SECTION, RECEIPT_MILEAGE_SECTION, RECEIPT_COST_DETAILS_SECTION,
    RECEIPT_EARNINGS_SECTION, RECEIPT_ROW_SELECTOR, RECEIPT_ROW_LABEL_SELECTOR,
    RECEIPT_ROW_VALUE_SELECTOR, RECEIPT_ROW_VALUE_NEGATIVE_SELECTOR, RECEIPT_ROW_VALUE_TOTAL_SELECTOR,
    RECEIPT_ROW_VALUE_EARNED_SELECTOR, RECEIPT_ROW_DETAILS_SELECTOR
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
            text = (await element.text_content() or '').strip() if element else None
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
            schedule_data['start_date'] = (await date_elements[0].text_content() or '').strip()
            schedule_data['end_date'] = (await date_elements[1].text_content() or '').strip()
        
        start_time_element = await page.query_selector(SCHEDULE_TIME_START_SELECTOR)
        if start_time_element:
            schedule_data['start_time'] = (await start_time_element.text_content() or '').strip()
        
        end_time_element = await page.query_selector(SCHEDULE_TIME_END_SELECTOR)
        if end_time_element:
            schedule_data['end_time'] = (await end_time_element.text_content() or '').strip()
            
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
            location_data['address'] = (await address_element.text_content() or '').strip()
            
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
            
            label_text = (await label_element.text_content() or '').strip()
            if not label_text:
                continue
            
            if 'Total Kilometers Included' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText')
                if value_element:
                    value_text = (await value_element.text_content() or '').strip()
                    if value_text:
                        km_match = extract_with_regex(value_text, r'([\d,]+)')
                        if km_match:
                            km_data['kilometers_included'] = int(km_match.replace(',', ''))
                
                overage_element = await section.query_selector(KILOMETERS_OVERAGE_SELECTOR)
                if overage_element:
                    overage_text = (await overage_element.text_content() or '').strip()
                    if overage_text:
                        rate_match = extract_with_regex(overage_text, r'\$([\d.]+)')
                        if rate_match:
                            km_data['overage_rate'] = float(rate_match)
            
            elif 'Kilometers driven' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText')
                if value_element:
                    value_text = (await value_element.text_content() or '').strip()
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
            
            label_text = (await label_element.text_content() or '').strip()
            if not label_text:
                continue
            
            if 'Total Earnings' in label_text or 'Earnings' in label_text:
                value_element = await section.query_selector('.css-14bos0l-StyledText span')
                if not value_element:
                    value_element = await section.query_selector('.css-14bos0l-StyledText')
                
                if value_element:
                    amount_text = (await value_element.text_content() or '').strip()
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
            protection_data['protection_plan'] = (await plan_element.text_content() or '').strip()
        
        deductible_element = await page.query_selector(PROTECTION_DEDUCTIBLE_SELECTOR)
        if deductible_element:
            deductible_text = (await deductible_element.text_content() or '').strip()
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

# ------------------------------ RECEIPT EXTRACTION ------------------------------

async def extract_receipt_row_data(row) -> Optional[Dict[str, Any]]:
    """Extract data from a receipt row (cost details or earnings row)."""
    try:
        # Try to find label - it might be directly in the row or in a nested div
        label_element = await row.query_selector(RECEIPT_ROW_LABEL_SELECTOR)
        if not label_element:
            # Try alternative: look for label in nested structure
            item_div = await row.query_selector('.css-1ffy8gg-StyledItemDottedLine')
            if item_div:
                label_element = await item_div.query_selector(RECEIPT_ROW_LABEL_SELECTOR)
        
        if not label_element:
            return None
        
        label_text = (await label_element.text_content() or '').strip()
        if not label_text:
            return None
        
        # Try to get value from different selectors
        # Try all selectors and use the one with actual content
        value_text = None
        value_numeric = None
        
        # Try all selectors in order of specificity
        selectors_to_try = [
            (RECEIPT_ROW_VALUE_NEGATIVE_SELECTOR, "negative"),  # Try negative first for fees
            (RECEIPT_ROW_VALUE_TOTAL_SELECTOR, "total"),
            (RECEIPT_ROW_VALUE_EARNED_SELECTOR, "earned"),
            (RECEIPT_ROW_VALUE_SELECTOR, "regular")
        ]
        
        for selector, selector_type in selectors_to_try:
            element = await row.query_selector(selector)
            if not element:
                # Try alternative: look for value in nested structure
                value_div = await row.query_selector('.css-2bo7kd-StyledValueDottedLine')
                if value_div:
                    element = await value_div.query_selector(selector)
            
            if element:
                text = (await element.text_content() or '').strip()
                # Only use this value if it has actual content
                if text:
                    value_text = text
                    value_numeric = parse_amount(text)
                    logger.debug(f"Found value using {selector_type} selector: '{text}' -> {value_numeric}")
                    break  # Found a value, stop trying other selectors
        
        # If still no value found, try searching for any value element in the row
        if not value_text:
            # Try to find value div and get any text content from it
            value_div = await row.query_selector('.css-2bo7kd-StyledValueDottedLine')
            if value_div:
                # Get all text from the value div
                div_text = (await value_div.text_content() or '').strip()
                if div_text:
                    value_text = div_text
                    value_numeric = parse_amount(div_text)
                    logger.debug(f"Found value from value div: '{div_text}' -> {value_numeric}")
        
        # Get details text if available (e.g., "6 days @ CA$43.83/day")
        details_text = None
        details_element = await row.query_selector(RECEIPT_ROW_DETAILS_SELECTOR)
        if details_element:
            details_text = (await details_element.text_content() or '').strip()
        
        return {
            'label': label_text,
            'value': value_text,
            'value_numeric': value_numeric,
            'details': details_text
        }
    except Exception as e:
        logger.debug(f"Error extracting receipt row data: {e}")
        return None

async def extract_receipt_data(page: Page, receipt_url: str) -> Dict[str, Any]:
    """Extract receipt data from a receipt page."""
    receipt_data = {
        'reservation_id': None,
        'host_name': None,
        'vehicle_name': None,
        'vehicle_year': None,
        'booked_date': None,
        'trip_start': None,
        'trip_end': None,
        'pickup_location': None,
        'return_location': None,
        'guest_name': None,
        'guest_id': None,
        'distance_included': None,
        'overage_rate': None,
        'turo_fees': None,
        'sales_tax': None,
        'cost_details': [],
        'earnings': [],
        'trip_price': None,
        'delivery_fee': None,
        'trip_total': None,
        'you_earned': None,
        'scraped_at': None
    }
    
    try:
        await page.goto(receipt_url, wait_until="domcontentloaded", timeout=TIMEOUT_PAGE_LOAD)
        await page.wait_for_timeout(3000)  # Wait for page to fully load (increased to 3 seconds)
        
        # Wait for receipt content to be visible
        try:
            # Wait for either the header or trip details section to appear
            await page.wait_for_selector(
                f"{RECEIPT_HEADER_SELECTOR}, {RECEIPT_TRIP_DETAILS_SECTION}",
                timeout=5000,
                state="visible"
            )
            await page.wait_for_timeout(1000)  # Additional wait for dynamic content
        except Exception as e:
            logger.debug(f"Receipt elements not found immediately, continuing anyway: {e}")
        
        # Extract reservation ID from header
        try:
            header = await page.query_selector(RECEIPT_HEADER_SELECTOR)
            if header:
                reservation_elements = await header.query_selector_all(RECEIPT_RESERVATION_ID_SELECTOR)
                for elem in reservation_elements:
                    text = (await elem.text_content() or '').strip()
                    if 'Reservation ID' in text:
                        reservation_id = extract_with_regex(text, r'Reservation ID\s+(\d+)')
                        if reservation_id:
                            receipt_data['reservation_id'] = reservation_id
                            break
        except Exception as e:
            logger.debug(f"Error extracting reservation ID: {e}")
        
        # Extract trip details section
        try:
            trip_details = await page.query_selector(RECEIPT_TRIP_DETAILS_SECTION)
            if trip_details:
                # Host name
                host_elem = await trip_details.query_selector(RECEIPT_HOST_NAME_SELECTOR)
                if host_elem:
                    receipt_data['host_name'] = (await host_elem.text_content() or '').strip()
                
                # Vehicle name and year
                vehicle_elem = await trip_details.query_selector(RECEIPT_VEHICLE_NAME_SELECTOR)
                if vehicle_elem:
                    vehicle_text = (await vehicle_elem.text_content() or '').strip()
                    receipt_data['vehicle_name'] = vehicle_text
                    # Extract year if present - only match valid years (1900-2099) to avoid false matches like "7020" from "Genesis G70"
                    year_match = extract_with_regex(vehicle_text, r'(19\d{2}|20\d{2})')
                    if year_match:
                        year_int = int(year_match)
                        # Validate year is in reasonable range
                        if 1900 <= year_int <= 2099:
                            receipt_data['vehicle_year'] = year_match
                
                # Booked date
                booked_elem = await trip_details.query_selector(RECEIPT_BOOKED_DATE_SELECTOR)
                if booked_elem:
                    booked_text = (await booked_elem.text_content() or '').strip()
                    if 'booked' in booked_text.lower():
                        receipt_data['booked_date'] = booked_text
                
                # Trip dates and locations - look for rows with labels
                rows = await trip_details.query_selector_all('[data-testid="row"]')
                current_label = None
                
                logger.debug(f"Found {len(rows)} rows in trip details section")
                
                for row in rows:
                    # Check if this row has a label (section header)
                    label_elem = await row.query_selector('.css-1z3l1r-StyledRow-titleRowStyles, .css-1uqof5-StyledText-styledSectionTitleStyles')
                    if label_elem:
                        current_label = (await label_elem.text_content() or '').strip()
                        logger.debug(f"Found label: {current_label}")
                        continue
                    
                    # If we have cells, extract data based on current label
                    cells = await row.query_selector_all('.css-on31fw, [data-testid="row"] > div')
                    if len(cells) >= 2:
                        cell1_text = (await cells[0].text_content() or '').strip()
                        cell2_text = (await cells[1].text_content() or '').strip()
                        
                        # Match based on label
                        if current_label:
                            label_lower = current_label.lower()
                            if 'trip start' in label_lower or 'trip dates' in label_lower:
                                receipt_data['trip_start'] = cell1_text
                                receipt_data['trip_end'] = cell2_text
                                logger.debug(f"Extracted trip dates: {cell1_text} | {cell2_text}")
                            elif 'pickup location' in label_lower or 'location' in label_lower:
                                receipt_data['pickup_location'] = cell1_text
                                receipt_data['return_location'] = cell2_text
                                logger.debug(f"Extracted locations: {cell1_text} | {cell2_text}")
                    
                    # Also try to find by text content directly
                    row_text = (await row.text_content() or '').strip()
                    if row_text and ('Trip start' in row_text or 'Trip end' in row_text):
                        # Try to extract dates from the row
                        date_parts = [p.strip() for p in row_text.split('\n') if p.strip()]
                        if len(date_parts) >= 2:
                            receipt_data['trip_start'] = date_parts[0]
                            receipt_data['trip_end'] = date_parts[1]
                            logger.debug(f"Extracted trip dates from text: {date_parts[0]} | {date_parts[1]}")
                    elif row_text and ('Pickup' in row_text or 'Return' in row_text):
                        # Try to extract locations from the row
                        location_parts = [p.strip() for p in row_text.split('\n') if p.strip()]
                        if len(location_parts) >= 2:
                            receipt_data['pickup_location'] = location_parts[0]
                            receipt_data['return_location'] = location_parts[1]
                            logger.debug(f"Extracted locations from text: {location_parts[0]} | {location_parts[1]}")
        except Exception as e:
            logger.debug(f"Error extracting trip details: {e}")
        
        # Extract guest section
        try:
            guest_section = await page.query_selector(RECEIPT_GUEST_SECTION)
            if guest_section:
                guest_link = await guest_section.query_selector('a[href*="/drivers/"]')
                if guest_link:
                    href = await guest_link.get_attribute('href')
                    if href:
                        guest_id = extract_with_regex(href, r'/drivers/(\d+)')
                        if guest_id:
                            receipt_data['guest_id'] = guest_id
                    guest_name = (await guest_link.text_content() or '').strip()
                    if guest_name:
                        receipt_data['guest_name'] = guest_name
        except Exception as e:
            logger.debug(f"Error extracting guest info: {e}")
        
        # Extract mileage section
        try:
            mileage_section = await page.query_selector(RECEIPT_MILEAGE_SECTION)
            if mileage_section:
                rows = await mileage_section.query_selector_all(RECEIPT_ROW_SELECTOR)
                for row in rows:
                    label_elem = await row.query_selector(RECEIPT_ROW_LABEL_SELECTOR)
                    value_elem = await row.query_selector(RECEIPT_ROW_VALUE_SELECTOR)
                    
                    if label_elem and value_elem:
                        label = (await label_elem.text_content() or '').strip()
                        value = (await value_elem.text_content() or '').strip()
                        
                        if 'Distance included' in label:
                            # Extract number and unit
                            km_match = extract_with_regex(value, r'(\d+)\s*km')
                            if km_match:
                                receipt_data['distance_included'] = int(km_match)
                        
                        # Extract overage rate from details
                        details_elem = await row.query_selector(RECEIPT_ROW_DETAILS_SELECTOR)
                        if details_elem:
                            details_text = (await details_elem.text_content() or '').strip()
                            if 'kilometer fee' in details_text:
                                rate_match = extract_with_regex(details_text, r'CA\$\s*([\d.]+)')
                                if rate_match:
                                    receipt_data['overage_rate'] = float(rate_match)
        except Exception as e:
            logger.debug(f"Error extracting mileage info: {e}")
        
        # Extract cost details section
        try:
            cost_section = await page.query_selector(RECEIPT_COST_DETAILS_SECTION)
            if cost_section:
                rows = await cost_section.query_selector_all(RECEIPT_ROW_SELECTOR)
                logger.debug(f"Found {len(rows)} rows in cost details section")
                for row in rows:
                    row_data = await extract_receipt_row_data(row)
                    if row_data:
                        label = row_data.get('label', '').lower()
                        value_numeric = row_data.get('value_numeric')
                        value_text = row_data.get('value', '')
                        
                        logger.debug(f"Cost details row - label: '{row_data.get('label')}', value: {value_text}, numeric: {value_numeric}")
                        
                        if 'trip total' in label:
                            receipt_data['trip_total'] = value_numeric
                            logger.debug(f"Extracted trip_total: {value_numeric}")
                        elif 'trip price' in label or 'base price' in label:
                            receipt_data['trip_price'] = value_numeric
                            logger.debug(f"Extracted trip_price: {value_numeric}")
                        elif 'delivery fee' in label or 'delivery' in label:
                            receipt_data['delivery_fee'] = value_numeric
                            logger.debug(f"Extracted delivery_fee: {value_numeric}")
                        # Check for turo fees first (most specific)
                        elif 'turo' in label and ('fee' in label or 'fees' in label):
                            if value_numeric is not None:
                                receipt_data['turo_fees'] = value_numeric
                                logger.info(f"✓ Extracted turo_fees: {value_numeric} from label '{row_data.get('label')}'")
                            else:
                                logger.warning(f"✗ turo_fees label found but value_numeric is None. Value text: '{value_text}'")
                        # Check for sales tax
                        elif 'sales tax' in label or ('tax' in label and 'sales' in label):
                            if value_numeric is not None:
                                receipt_data['sales_tax'] = value_numeric
                                logger.info(f"✓ Extracted sales_tax: {value_numeric} from label '{row_data.get('label')}'")
                            else:
                                logger.warning(f"✗ sales_tax label found but value_numeric is None. Value text: '{value_text}'")
                        # Fallback for turo (without explicit fee)
                        elif 'turo' in label:
                            if value_numeric is not None and not receipt_data.get('turo_fees'):
                                receipt_data['turo_fees'] = value_numeric
                                logger.debug(f"Extracted turo_fees (fallback): {value_numeric}")
                        # Fallback for tax (without explicit sales)
                        elif 'tax' in label and not receipt_data.get('sales_tax'):
                            if value_numeric is not None:
                                receipt_data['sales_tax'] = value_numeric
                                logger.debug(f"Extracted sales_tax (fallback): {value_numeric}")
                        else:
                            receipt_data['cost_details'].append(row_data)
        except Exception as e:
            logger.debug(f"Error extracting cost details: {e}")
        
        # Extract earnings section
        try:
            earnings_section = await page.query_selector(RECEIPT_EARNINGS_SECTION)
            if earnings_section:
                rows = await earnings_section.query_selector_all(RECEIPT_ROW_SELECTOR)
                logger.debug(f"Found {len(rows)} rows in earnings section")
                for row in rows:
                    row_data = await extract_receipt_row_data(row)
                    if row_data:
                        label = row_data.get('label', '').lower()
                        value_numeric = row_data.get('value_numeric')
                        value_text = row_data.get('value', '')
                        
                        logger.debug(f"Earnings row - label: '{row_data.get('label')}', value: {value_text}, numeric: {value_numeric}")
                        
                        # Check for turo fees first (most specific)
                        if 'turo' in label and ('fee' in label or 'fees' in label):
                            if value_numeric is not None:
                                receipt_data['turo_fees'] = value_numeric
                                logger.info(f"✓ Extracted turo_fees: {value_numeric} from label '{row_data.get('label')}'")
                            else:
                                logger.warning(f"✗ turo_fees label found but value_numeric is None. Value text: '{value_text}'")
                        # Check for sales tax
                        elif 'sales tax' in label or ('tax' in label and 'sales' in label):
                            if value_numeric is not None:
                                receipt_data['sales_tax'] = value_numeric
                                logger.info(f"✓ Extracted sales_tax: {value_numeric} from label '{row_data.get('label')}'")
                            else:
                                logger.warning(f"✗ sales_tax label found but value_numeric is None. Value text: '{value_text}'")
                        # Check for you earned
                        elif 'you earned' in label:
                            if value_numeric is not None:
                                receipt_data['you_earned'] = value_numeric
                                logger.debug(f"Extracted you_earned: {value_numeric}")
                        # Fallback for turo (without explicit fee)
                        elif 'turo' in label:
                            if value_numeric is not None and not receipt_data.get('turo_fees'):
                                receipt_data['turo_fees'] = value_numeric
                                logger.debug(f"Extracted turo_fees (fallback): {value_numeric}")
                        # Fallback for tax (without explicit sales)
                        elif 'tax' in label and not receipt_data.get('sales_tax'):
                            if value_numeric is not None:
                                receipt_data['sales_tax'] = value_numeric
                                logger.debug(f"Extracted sales_tax (fallback): {value_numeric}")
                        else:
                            receipt_data['earnings'].append(row_data)
            else:
                logger.debug("Earnings section not found")
        except Exception as e:
            logger.debug(f"Error extracting earnings: {e}")
        
        receipt_data['scraped_at'] = datetime.utcnow().isoformat()
        
        # Log summary of extracted data
        logger.info(
            f"Receipt extraction summary for {receipt_data.get('reservation_id', 'unknown')}: "
            f"trip_price={receipt_data.get('trip_price')}, "
            f"delivery_fee={receipt_data.get('delivery_fee')}, "
            f"trip_total={receipt_data.get('trip_total')}, "
            f"turo_fees={receipt_data.get('turo_fees')}, "
            f"sales_tax={receipt_data.get('sales_tax')}, "
            f"you_earned={receipt_data.get('you_earned')}"
        )
        
    except Exception as e:
        logger.error(f"Error extracting receipt data from {receipt_url}: {e}")
        receipt_data['error'] = str(e)
    
    return receipt_data
