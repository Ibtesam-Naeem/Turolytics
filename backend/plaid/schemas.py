# ------------------------------ IMPORTS ------------------------------
from pydantic import BaseModel, field_serializer
from typing import Optional, List, Any, Dict
from datetime import datetime
from decimal import Decimal

# ------------------------------ BASE MODELS ------------------------------

class BaseOutModel(BaseModel):
    """Base model with common datetime serialization."""
    
    @field_serializer('created_at', 'updated_at', 'date', 'last_sync_at', check_fields=False)
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None
    
    class Config:
        from_attributes = True

# ------------------------------ OUTPUT MODELS ------------------------------

class PlaidIntegrationOut(BaseOutModel):
    """Plaid integration output model."""
    id: int
    account_id: int
    item_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PlaidAccountOut(BaseOutModel):
    """Plaid account output model."""
    id: int
    plaid_integration_id: int
    account_id: int
    plaid_account_id: str
    name: str
    official_name: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    mask: Optional[str] = None
    is_active: bool
    balance_current: Optional[str] = None
    balance_available: Optional[str] = None
    balance_limit: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TransactionOut(BaseOutModel):
    """Transaction output model."""
    id: int
    account_id: int
    plaid_account_id: int
    plaid_transaction_id: str
    date: datetime
    amount: Decimal
    merchant_name: Optional[str] = None
    name: str
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    is_vehicle_related: bool
    vehicle_category: Optional[str] = None
    transaction_type: Optional[str] = None
    match_confidence: Optional[Decimal] = None
    document_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TransactionDetailOut(TransactionOut):
    """Detailed transaction output model with full data."""
    plaid_category: Optional[List[str]] = None
    plaid_data: Optional[Dict[str, Any]] = None

# ------------------------------ REQUEST MODELS ------------------------------

class LinkTokenRequest(BaseModel):
    """Request to create Link token."""
    account_id: int
    user_id: Optional[str] = None

class PublicTokenExchangeRequest(BaseModel):
    """Request to exchange public token."""
    public_token: str
    account_id: int

class TransactionSyncRequest(BaseModel):
    """Request to sync transactions."""
    account_id: int
    cursor: Optional[str] = None
    days_back: Optional[int] = 90

class TransactionGetRequest(BaseModel):
    """Request to get transactions."""
    account_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    account_ids: Optional[List[str]] = None
    vehicle_related_only: bool = False
    transaction_type: Optional[str] = None  # 'expense' or 'revenue'
    vehicle_category: Optional[str] = None

class AccountToggleRequest(BaseModel):
    """Request to toggle account monitoring."""
    account_id: int
    plaid_account_id: int
    is_active: bool

class TransactionLinkReceiptRequest(BaseModel):
    """Request to link transaction to receipt."""
    account_id: int
    transaction_id: int
    document_id: int

# ------------------------------ RESPONSE MODELS ------------------------------

class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    data: Dict[str, Any]

# ------------------------------ END OF FILE ------------------------------

