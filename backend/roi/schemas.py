# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ------------------------------ ROI SCHEMAS ------------------------------

class ROICalculationCreate(BaseModel):
    """Schema for creating a new ROI calculation."""
    vehicle_name: str
    vehicle_price: float
    daily_rate: float
    booking_days: int
    monthly_expenses: float
    insurance_monthly: float
    annual_depreciation: float
    roi: float
    annual_profit: float

class ROICalculationUpdate(BaseModel):
    """Schema for updating an existing ROI calculation."""
    vehicle_name: Optional[str] = None
    vehicle_price: Optional[float] = None
    daily_rate: Optional[float] = None
    booking_days: Optional[int] = None
    monthly_expenses: Optional[float] = None
    insurance_monthly: Optional[float] = None
    annual_depreciation: Optional[float] = None
    roi: Optional[float] = None
    annual_profit: Optional[float] = None

class ROICalculationOut(BaseModel):
    """Schema for ROI calculation output."""
    id: int
    vehicle_name: str
    vehicle_price: float
    daily_rate: float
    booking_days: int
    monthly_expenses: float
    insurance_monthly: float
    annual_depreciation: float
    roi: float
    annual_profit: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: dict
    message: Optional[str] = None
