# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel, field_serializer
from typing import Optional, List, Any
from datetime import datetime

# ------------------------------ BASE MODELS ------------------------------

class BaseOutModel(BaseModel):
    """Base model with common datetime serialization."""
    
    @field_serializer('created_at', 'updated_at', 'scraped_at', check_fields=False)
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None
    
    class Config:
        from_attributes = True

class TripOut(BaseOutModel):
    """Trip output model."""
    id: int
    trip_id: str
    trip_url: Optional[str] = None
    vehicle_id: Optional[int] = None
    customer_name: Optional[str] = None
    status: str
    trip_type: Optional[str] = None
    cancellation_info: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancelled_date: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    location_type: Optional[str] = None
    address: Optional[str] = None
    kilometers_driven: Optional[int] = None
    kilometers_included: Optional[int] = None
    overage_rate: Optional[float] = None
    total_earnings: Optional[float] = None
    protection_plan: Optional[str] = None
    deductible: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

class VehicleOut(BaseOutModel):
    """Vehicle output model."""
    id: int
    name: str
    year: Optional[str] = None
    trim: Optional[str] = None
    license_plate: Optional[str] = None
    status: Optional[str] = None
    trip_info: Optional[str] = None
    rating: Optional[float] = None
    trip_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

class ReviewOut(BaseOutModel):
    """Review output model."""
    id: int
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    vehicle_id: Optional[int] = None
    rating: Optional[float] = None
    date: Optional[datetime] = None
    vehicle_info: Optional[str] = None
    review_text: Optional[str] = None
    areas_of_improvement: List[str] = []
    host_response: Optional[str] = None
    has_host_response: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

class EarningsBreakdownOut(BaseOutModel):
    """Earnings breakdown output model."""
    id: int
    type: str
    amount: Optional[str] = None
    amount_numeric: Optional[float] = None
    year: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

class VehicleEarningsOut(BaseOutModel):
    """Vehicle earnings output model."""
    id: int
    vehicle_name: str
    license_plate: Optional[str] = None
    trim: Optional[str] = None
    earnings_amount: Optional[str] = None
    earnings_amount_numeric: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None

# ------------------------------ RESPONSE MODELS ------------------------------

class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    data: dict[str, Any]

# ------------------------------ END OF FILE ------------------------------
