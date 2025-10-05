# ------------------------------ IMPORTS ------------------------------
import re
from typing import Any, Optional

# ------------------------------ COMPILED REGEX PATTERNS ------------------------------
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')

# ------------------------------ PARSING HELPERS ------------------------------

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string like '$100.00' into a float."""
    if not amount_str:
        return None
    
    try:
        cleaned = amount_str.replace('$', '').replace(',', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to integer."""
    if value is None:
        return None
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# ------------------------------ STRING HELPERS ------------------------------

def clean_string(value: str) -> Optional[str]:
    """Clean and normalize string value."""
    if not value or not isinstance(value, str):
        return None
    
    cleaned = value.strip()
    return cleaned if cleaned else None


def truncate_string(value: str, max_length: int = 255) -> str:
    """Truncate string to maximum length."""
    if not value:
        return ""
    
    return value[:max_length] if len(value) > max_length else value

# ------------------------------ VALIDATION HELPERS ------------------------------

def is_valid_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    
    return bool(EMAIL_PATTERN.match(email.strip()))

def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False
    
    return bool(URL_PATTERN.match(url.strip()))

# ------------------------------ DATA HELPERS ------------------------------

def extract_vehicle_info(vehicle_name: str) -> dict:
    """Extract year, make, model from vehicle name string."""
    if not vehicle_name:
        return {"full_name": None, "year": None, "make": None, "model": None}
    
    # Clean the vehicle name - remove status prefixes and extra text
    cleaned_name = vehicle_name
    
    # Remove common status prefixes
    status_prefixes = ['Snoozed', 'Listed', 'Unavailable', 'Maintenance']
    for prefix in status_prefixes:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix):].strip()
            break
    
    # Remove extra text after the vehicle info (like "No trips", "Vehicle actions", etc.)
    # Look for patterns like "• BZEJ166" or "No trips" or "Vehicle actions"
    extra_patterns = [
        r' • [A-Z0-9]+.*',  # License plate and everything after
        r'No trips.*',       # "No trips" and everything after
        r'Vehicle actions.*', # "Vehicle actions" and everything after
        r'Last trip:.*',     # "Last trip:" and everything after
    ]
    
    for pattern in extra_patterns:
        cleaned_name = re.sub(pattern, '', cleaned_name).strip()
    
    # Now try to parse make, model, year
    parts = cleaned_name.split()
    if len(parts) >= 3:
        # Look for year (4 digits) in the parts
        year = None
        year_index = -1
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4 and 1900 <= int(part) <= 2030:
                year = int(part)
                year_index = i
                break
        
        if year is not None:
            if year_index == 0:  # Year first: "2017 Audi Q7"
                make = parts[1] if len(parts) > 1 else None
                model = ' '.join(parts[2:]) if len(parts) > 2 else None
            elif year_index == len(parts) - 1:  # Year last: "Audi Q7 2017"
                make = parts[0] if len(parts) > 1 else None
                model = ' '.join(parts[1:year_index]) if year_index > 1 else None
            else:  # Year in middle: "Audi 2017 Q7"
                make = parts[0] if year_index > 0 else None
                model = ' '.join(parts[year_index+1:]) if year_index < len(parts) - 1 else None
            
            return {
                "full_name": f"{make} {model} {year}".strip() if make and model else cleaned_name,
                "year": year,
                "make": make,
                "model": model
            }
    
    # Fallback: try to extract year from anywhere in the string
    year_match = re.search(r'\b(19|20)\d{2}\b', cleaned_name)
    if year_match:
        year = int(year_match.group())
        # Remove year from the string and try to parse make/model
        without_year = re.sub(r'\b(19|20)\d{2}\b', '', cleaned_name).strip()
        parts = without_year.split()
        if len(parts) >= 2:
            make = parts[0]
            model = ' '.join(parts[1:])
            return {
                "full_name": f"{make} {model} {year}".strip(),
                "year": year,
                "make": make,
                "model": model
            }
    
    return {"full_name": cleaned_name, "year": None, "make": None, "model": None}

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number format."""
    if not phone:
        return None
    
    digits = ''.join(filter(str.isdigit, phone))
    
    if 10 <= len(digits) <= 15:
        return digits
    
    return None


# ------------------------------ END OF FILE ------------------------------
