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
    
    parts = vehicle_name.split()
    if len(parts) >= 3 and parts[-1].isdigit():
        return {
            "full_name": vehicle_name,
            "year": int(parts[-1]),
            "make": parts[0],
            "model": ' '.join(parts[1:-1])
        }
    
    return {"full_name": vehicle_name, "year": None, "make": None, "model": None}

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number format."""
    if not phone:
        return None
    
    digits = ''.join(filter(str.isdigit, phone))
    
    if 10 <= len(digits) <= 15:
        return digits
    
    return None


# ------------------------------ END OF FILE ------------------------------
