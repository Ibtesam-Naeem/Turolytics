# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from core.database.models.s3 import DocumentCategory
from turo.schemas import BaseOutModel

# ------------------------------ DOCUMENT SCHEMAS ------------------------------

class DocumentOut(BaseOutModel):
    """Document output model."""
    id: int
    account_id: int
    vehicle_id: Optional[int] = None
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    category: DocumentCategory
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DocumentUpdateRequest(BaseModel):
    """Document update request model."""
    category: Optional[DocumentCategory] = None
    vehicle_id: Optional[int] = None
    description: Optional[str] = None

# ------------------------------ END OF FILE ------------------------------

