# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel, EmailStr
from typing import Optional

# ------------------------------ SCHEMAS ------------------------------

class WaitlistRequest(BaseModel):
    """Waitlist signup request model."""
    email: EmailStr
    vehicleCount: Optional[str] = None
    trackingProduct: Optional[str] = None
    trackingProductOther: Optional[str] = None
    wouldUse: Optional[str] = None
    priceWilling: Optional[str] = None
    feedback: Optional[str] = None

# ------------------------------ END OF FILE ------------------------------