# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.schemas import APIResponse
from core.utils.route_helpers import (
    handle_route_errors,
    success_response,
)
from .service import WaitlistService
from .schemas import WaitlistRequest

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_waitlist_service(db: Session = Depends(get_db)) -> WaitlistService:
    """Get WaitlistService instance."""
    return WaitlistService(db=db)

# ------------------------------ ROUTES ------------------------------

@router.post("/waitlist", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
@handle_route_errors("joining waitlist")
async def join_waitlist(
    request: WaitlistRequest,
    service: WaitlistService = Depends(get_waitlist_service)
):
    """Add an email to the waitlist. Returns success if email is added or already exists."""
    result = service.join_waitlist(request)
    return success_response(data=result.to_dict())
