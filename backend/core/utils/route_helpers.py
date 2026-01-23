# ------------------------------ IMPORTS ------------------------------
from functools import wraps
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Callable, Any, Optional, Dict
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# ------------------------------ RESPONSE MODELS ------------------------------

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None

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
                raise

            except Exception as e:
                if rollback_db:
                    db = kwargs.get('db') or next((arg for arg in args if hasattr(arg, 'rollback')), None)
                    if db:
                        try:
                            db.rollback()
                        except Exception:
                            pass  
                
                logger.exception(f"Error in {operation_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {str(e)}"
                )
        return wrapper
    return decorator

# ------------------------------ UTILITY FUNCTIONS ------------------------------

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

# ------------------------------ END OF FILE ------------------------------

