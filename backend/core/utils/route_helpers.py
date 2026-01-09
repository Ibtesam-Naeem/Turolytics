# ------------------------------ IMPORTS ------------------------------
from functools import wraps
from fastapi import HTTPException
from typing import Callable, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# ------------------------------ ERROR HANDLING ------------------------------

def handle_route_errors(operation_name: str, rollback_db: bool = False):
    """
    Decorator to handle common route errors.
    Automatically catches exceptions, logs them, and raises appropriate HTTPExceptions.
    HTTPExceptions are re-raised as-is (no double-wrapping).
    
    Args:
        operation_name: Name of the operation for logging
        rollback_db: If True, attempts to rollback database session on error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions as-is (they're already properly formatted)
                raise
            except Exception as e:
                # Attempt to rollback database if requested
                if rollback_db:
                    # Try to find db session in kwargs or args
                    db = kwargs.get('db') or next((arg for arg in args if hasattr(arg, 'rollback')), None)
                    if db:
                        try:
                            db.rollback()
                        except Exception:
                            pass  # Ignore rollback errors
                
                logger.exception(f"Error in {operation_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {str(e)}"
                )
        return wrapper
    return decorator

# ------------------------------ UTILITY FUNCTIONS ------------------------------

def parse_amount(amount_str: Optional[str]) -> Optional[float]:
    """
    Parse amount string like '$100.00', 'CA$1,234.56', or '$1,234.56' into a float.
    Handles None, empty strings, and various formats including CA$ prefix.
    Also handles negative values like '- CA$12.60'.
    """
    if not amount_str:
        return None
    try:
        # Remove currency symbols (including CA$ prefix), commas, and ALL whitespace
        cleaned = str(amount_str).replace("CA$", "").replace("$", "").replace(",", "").replace(" ", "")
        # Handle empty string after cleaning (e.g., "CA$0" -> "0")
        if not cleaned:
            return 0.0
        return float(cleaned)
    except (ValueError, TypeError, AttributeError):
        return None

# ------------------------------ INTEGRATION HELPERS ------------------------------

def get_turo_integration(db: Session, account_id: int):
    """Get Turo integration for an account."""
    from core.database.models.turo_integration import TuroIntegration
    return db.query(TuroIntegration).filter(
        TuroIntegration.account_id == account_id
    ).first()

def get_bouncie_integration(db: Session, account_id: int):
    """Get Bouncie integration for an account."""
    from core.database.models.bouncie_integration import BouncieIntegration
    return db.query(BouncieIntegration).filter(
        BouncieIntegration.account_id == account_id
    ).first()

# ------------------------------ END OF FILE ------------------------------

