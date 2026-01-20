# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime

# ------------------------------ BASE MODELS ------------------------------

class BaseOutModel(BaseModel):
    """
    Base model with common datetime serialization.
    Handles all common datetime fields used across different modules.
    """
    
    @field_serializer(
        'created_at', 
        'updated_at', 
        'scraped_at', 
        'listed_on_turo_date', 
        'removed_from_turo_date',
        'bouncie_earliest_start', 
        'bouncie_latest_end',
        'occurred_at',
        'cleared_at',
        'date',
        check_fields=False
    )
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return dt.isoformat() if dt else None
    
    class Config:
        from_attributes = True

# ------------------------------ RESPONSE MODELS ------------------------------

class APIResponse(BaseModel):
    """
    Standard API response wrapper used across all endpoints.
    Provides consistent response structure with optional message field.
    """
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None

# ------------------------------ END OF FILE ------------------------------
