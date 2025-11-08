# ------------------------------ IMPORTS ------------------------------
import re
from typing import Optional

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

def extract_with_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Extract text using regex pattern."""
    if not text:
        return None
    match = re.search(pattern, text)
    return match.group(group) if match else None


# ------------------------------ END OF FILE ------------------------------
