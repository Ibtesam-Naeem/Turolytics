# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from services.plaid_service import PlaidService
from database.operations.plaid import get_plaid_data, delete_plaid_data

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ ROUTER ------------------------------
router = APIRouter(prefix="/plaid", tags=["plaid"])

# ------------------------------ PYDANTIC MODELS ------------------------------
class LinkTokenRequest(BaseModel):
    """Request model for creating link token."""
    user_id: str
    products: Optional[List[str]] = None

class LinkTokenResponse(BaseModel):
    """Response model for link token."""
    success: bool
    link_token: Optional[str] = None
    expiration: Optional[str] = None
    products: Optional[List[str]] = None
    error: Optional[str] = None

class ExchangeTokenRequest(BaseModel):
    """Request model for exchanging public token."""
    public_token: str
    user_id: str

class ExchangeTokenResponse(BaseModel):
    """Response model for token exchange."""
    success: bool
    access_token: Optional[str] = None
    item_id: Optional[str] = None
    error: Optional[str] = None

class SyncDataRequest(BaseModel):
    """Request model for syncing data."""
    user_id: str
    access_token: Optional[str] = None

class SyncDataResponse(BaseModel):
    """Response model for data sync."""
    success: bool
    accounts: Optional[Dict[str, Any]] = None
    transactions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ------------------------------ DEPENDENCIES ------------------------------
def get_plaid_service() -> PlaidService:
    """Get Plaid service instance."""
    return PlaidService()

# ------------------------------ ENDPOINTS ------------------------------
@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    request: LinkTokenRequest,
    plaid_service: PlaidService = Depends(get_plaid_service)
):
    """Create a Plaid link token for user authentication.
    
    Args:
        request: Link token request data
        plaid_service: Plaid service instance
        
    Returns:
        Link token response
    """
    try:
        logger.info(f"Creating link token for user: {request.user_id}")
        
        result = plaid_service.create_link_token(request.user_id, request.products)
        
        return LinkTokenResponse(
            success=result["success"],
            link_token=result.get("link_token"),
            expiration=result.get("expiration"),
            products=result.get("products"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create link token: {str(e)}"
        )

@router.post("/exchange-token", response_model=ExchangeTokenResponse)
async def exchange_public_token(
    request: ExchangeTokenRequest,
    plaid_service: PlaidService = Depends(get_plaid_service)
):
    """Exchange public token for access token.
    
    Args:
        request: Exchange token request data
        plaid_service: Plaid service instance
        
    Returns:
        Exchange token response
    """
    try:
        logger.info(f"Exchanging public token for user: {request.user_id}")
        
        result = plaid_service.exchange_public_token(request.public_token, request.user_id)
        
        return ExchangeTokenResponse(
            success=result["success"],
            access_token=result.get("access_token"),
            item_id=result.get("item_id"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error exchanging public token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange public token: {str(e)}"
        )

@router.get("/accounts/{user_id}")
async def get_accounts(
    user_id: str,
    plaid_service: PlaidService = Depends(get_plaid_service)
):
    """Get Plaid accounts for a user.
    
    Args:
        user_id: User identifier
        plaid_service: Plaid service instance
        
    Returns:
        Account data
    """
    try:
        logger.info(f"Getting accounts for user: {user_id}")
        
        result = plaid_service.get_and_save_accounts(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get accounts")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accounts: {str(e)}"
        )

@router.get("/transactions/{user_id}")
async def get_transactions(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: int = 100,
    plaid_service: PlaidService = Depends(get_plaid_service)
):
    """Get Plaid transactions for a user.
    
    Args:
        user_id: User identifier
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        count: Number of transactions to retrieve
        plaid_service: Plaid service instance
        
    Returns:
        Transaction data
    """
    try:
        logger.info(f"Getting transactions for user: {user_id}")
        
        result = plaid_service.get_and_save_transactions(
            user_id, start_date, end_date, count
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get transactions")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {str(e)}"
        )

@router.post("/sync/{user_id}", response_model=SyncDataResponse)
async def sync_user_data(
    user_id: str,
    request: Optional[SyncDataRequest] = None,
    plaid_service: PlaidService = Depends(get_plaid_service)
):
    """Sync all Plaid data for a user.
    
    Args:
        user_id: User identifier
        request: Optional sync request data
        plaid_service: Plaid service instance
        
    Returns:
        Sync data response
    """
    try:
        logger.info(f"Syncing data for user: {user_id}")
        
        access_token = request.access_token if request else None
        result = plaid_service.sync_user_data(user_id, access_token)
        
        return SyncDataResponse(
            success=result["success"],
            accounts=result.get("accounts"),
            transactions=result.get("transactions"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error syncing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync data: {str(e)}"
        )

@router.get("/data/{user_id}")
async def get_stored_data(user_id: str):
    """Get stored Plaid data for a user from database.
    
    Args:
        user_id: User identifier
        
    Returns:
        Stored data
    """
    try:
        logger.info(f"Getting stored data for user: {user_id}")
        
        result = get_plaid_data(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get stored data")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stored data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stored data: {str(e)}"
        )

@router.delete("/data/{user_id}")
async def delete_user_data(user_id: str):
    """Delete all Plaid data for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Deletion result
    """
    try:
        logger.info(f"Deleting Plaid data for user: {user_id}")
        
        success = delete_plaid_data(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete Plaid data"
            )
        
        return {"success": True, "message": "Plaid data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Plaid data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Plaid data: {str(e)}"
        )

@router.get("/test-connection")
async def test_connection(plaid_service: PlaidService = Depends(get_plaid_service)):
    """Test Plaid connection.
    
    Args:
        plaid_service: Plaid service instance
        
    Returns:
        Connection test result
    """
    try:
        logger.info("Testing Plaid connection")
        
        result = plaid_service.test_connection()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Plaid connection failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )
