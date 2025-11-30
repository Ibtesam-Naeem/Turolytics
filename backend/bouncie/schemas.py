# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel, field_serializer
from typing import Optional, List, Any, Dict
from datetime import datetime

# ------------------------------ BASE MODELS ------------------------------

class BaseOutModel(BaseModel):
    """Base model with common datetime serialization."""
    
    @field_serializer('created_at', 'updated_at', 'bouncie_earliest_start', 'bouncie_latest_end', check_fields=False)
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None
    
    class Config:
        from_attributes = True

# ------------------------------ OUTPUT MODELS ------------------------------

class BouncieTripMatchOut(BaseOutModel):
    """Bouncie trip match output model."""
    id: int
    trip_id: Optional[str] = None 
    turo_trip_id: int
    bouncie_trip_count: int
    aggregated_distance_km: Optional[float] = None
    aggregated_distance_miles: Optional[float] = None
    total_duration_hours: Optional[float] = None
    coordinate_count: Optional[int] = None
    has_polyline: bool = False
    has_coordinates: bool = False
    has_match_data: bool = False
    bouncie_earliest_start: Optional[datetime] = None
    bouncie_latest_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BouncieTripMatchDetailOut(BouncieTripMatchOut):
    """Detailed Bouncie trip match output model with full data."""
    coordinates: Optional[List[List[float]]] = None
    polyline: Optional[str] = None
    match_data: Optional[Dict[str, Any]] = None

class BouncieVehicleMappingOut(BaseOutModel):
    """Bouncie vehicle mapping output model."""
    id: int
    vehicle_id: int
    vehicle_name: Optional[str] = None
    imei: str
    bouncie_nickname: Optional[str] = None
    bouncie_vin: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ------------------------------ REQUEST MODELS ------------------------------

class MatchRequest(BaseModel):
    account_id: int
    authorization_code: Optional[str] = None
    trip_id: Optional[str] = None
    imei: Optional[str] = None
    days_back: int = 30

class VehicleMappingRequest(BaseModel):
    account_id: int
    vehicle_id: int
    imei: str
    bouncie_nickname: Optional[str] = None
    bouncie_vin: Optional[str] = None

class VehicleMappingUpdateRequest(BaseModel):
    """Request model for updating vehicle mappings."""
    vehicle_id: Optional[int] = None
    imei: Optional[str] = None
    bouncie_nickname: Optional[str] = None
    bouncie_vin: Optional[str] = None

# ------------------------------ RESPONSE MODELS ------------------------------

class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    data: Dict[str, Any]

# ------------------------------ END OF FILE ------------------------------

