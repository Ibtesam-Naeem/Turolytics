# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import Optional

# ------------------------------ HELPER FUNCTIONS ------------------------------

def format_date_for_api(date: datetime) -> str:
    """Format datetime for Plaid API (YYYY-MM-DD)."""
    return date.strftime("%Y-%m-%d")

def parse_plaid_date(date_str: str) -> Optional[datetime]:
    """Parse Plaid date string to datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def format_amount(amount: float) -> str:
    """Format amount as string for storage (preserves precision)."""
    return str(amount)

def parse_amount(amount_str: str) -> float:
    """Parse amount string to float."""
    try:
        return float(amount_str)
    except (ValueError, TypeError):
        return 0.0

