# ------------------------------ IMPORTS ------------------------------
from functools import wraps
from fastapi import HTTPException
from typing import Callable, Any, Optional, List, Dict, Type
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from core.schemas import APIResponse

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

def get_resource_or_404(
    db: Session,
    model: Type[Any],
    resource_id: int,
    account_id: int,
    resource_name: str = "Resource"
) -> Any:
    """
    Get a resource by ID and account_id, or raise 404 if not found.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        resource_id: Resource ID to find
        account_id: Account ID to verify ownership
        resource_name: Name for error message (e.g., "ROI calculation", "Vehicle mapping")
    
    Returns:
        Resource instance
    
    Raises:
        HTTPException: 404 if resource not found
    """
    resource = db.query(model).filter(
        model.id == resource_id,
        model.account_id == account_id
    ).first()
    
    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"{resource_name} {resource_id} not found"
        )
    
    return resource

def update_resource_fields(
    db: Session,
    resource: Any,
    update_data: Dict[str, Any],
    commit: bool = True
) -> Any:
    """
    Update resource fields from a dictionary.
    
    Args:
        db: Database session
        resource: Resource instance to update
        update_data: Dictionary of field: value pairs
        commit: Whether to commit the transaction
    
    Returns:
        Updated resource instance
    """
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    if commit:
        db.commit()
        db.refresh(resource)
    
    return resource

def calculate_waitlist_position(
    db: Session,
    model: Type[Any],
    entry_created_at: datetime,
    account_id_field: Optional[str] = None,
    account_id: Optional[int] = None
) -> Dict[str, int]:
    """
    Calculate waitlist position and total count for an entry.
    
    Args:
        db: Database session
        model: Waitlist model class
        entry_created_at: Created timestamp of the entry
        account_id_field: Optional field name for account filtering (if None, no filtering)
        account_id: Optional account ID to filter by
    
    Returns:
        Dictionary with 'position' and 'total' keys
    """
    query = db.query(model)
    
    # Apply account filter if provided
    if account_id_field and account_id:
        query = query.filter(getattr(model, account_id_field) == account_id)
    
    # Calculate position: count entries created at or before this entry
    position = query.filter(model.created_at <= entry_created_at).count()
    total = query.count()
    
    return {"position": position, "total": total}

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

def require_integration(integration, integration_name: str = "Integration"):
    """
    Raise HTTPException if integration is None.
    
    Args:
        integration: The integration object (or None)
        integration_name: Name for error message (e.g., "Turo", "Bouncie")
    
    Raises:
        HTTPException: If integration is None
    """
    if not integration:
        raise HTTPException(
            status_code=404,
            detail=f"No {integration_name} integration found for this account"
        )
    return integration

def not_connected_response(integration_name: str = "Integration") -> "APIResponse":
    """
    Create a response for when integration is not connected.
    
    Args:
        integration_name: Name of the integration (e.g., "Turo", "Bouncie")
    
    Returns:
        APIResponse indicating not connected
    """
    return APIResponse(
        success=True,
        data={
            "connected": False,
            "message": f"No {integration_name} integration found for this account"
        }
    )

# ------------------------------ RESPONSE BUILDERS ------------------------------

def success_response(data: Dict[str, Any], message: Optional[str] = None) -> APIResponse:
    """
    Create a standardized success API response.
    
    Args:
        data: Response data dictionary
        message: Optional success message
    
    Returns:
        APIResponse with success=True
    """
    return APIResponse(success=True, data=data, message=message)

def list_response(
    items: List[Any], 
    key: str = "items", 
    total: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> APIResponse:
    """
    Create a standardized list response with pagination metadata.
    
    Args:
        items: List of items to return
        key: Key name for items in response data (default: "items")
        total: Total count (if None, uses len(items))
        limit: Pagination limit
        offset: Pagination offset
    
    Returns:
        APIResponse with list data and metadata
    """
    response_data = {key: items, "total": total if total is not None else len(items)}
    if limit is not None:
        response_data["limit"] = limit
    if offset is not None:
        response_data["offset"] = offset
    return APIResponse(success=True, data=response_data)

def error_response(message: str, status_code: int = 400) -> HTTPException:
    """
    Create a standardized error response.
    Note: This returns an HTTPException, not an APIResponse, to maintain FastAPI error handling.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
    
    Returns:
        HTTPException to be raised
    """
    return HTTPException(status_code=status_code, detail=message)

# ------------------------------ END OF FILE ------------------------------

