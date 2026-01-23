# ------------------------------ IMPORTS ------------------------------
import os
import hmac
import time
from collections import defaultdict, deque
from fastapi import APIRouter, Depends, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from core.config.settings import settings
from core.utils.route_helpers import (
    APIResponse,
    handle_route_errors,
    success_response,
)
from .service import WaitlistService
from .schemas import WaitlistRequest
from .auth import (
    generate_session_token,
    require_waitlist_auth,
    SESSION_COOKIE_NAME,
)

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

# ------------------------------ ADMIN ROUTES ------------------------------

class PasswordRequest(BaseModel):
    """Password authentication request."""
    password: str

# ------------------------------ RATE LIMITING ------------------------------
_AUTH_ATTEMPTS: dict[str, "deque[float]"] = defaultdict(deque)

def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _rate_limit_auth(request: Request) -> Optional[int]:
    """Returns retry_after seconds if rate-limited, otherwise None."""
    max_attempts = int(os.getenv("WAITLIST_AUTH_RATE_LIMIT_MAX", "10"))
    window_seconds = int(os.getenv("WAITLIST_AUTH_RATE_LIMIT_WINDOW_SECONDS", "300"))

    now = time.time()
    ip = _get_client_ip(request)
    q = _AUTH_ATTEMPTS[ip]

    cutoff = now - window_seconds
    while q and q[0] < cutoff:
        q.popleft()

    if len(q) >= max_attempts:
        retry_after = int((q[0] + window_seconds) - now) + 1
        return max(1, retry_after)

    q.append(now)
    return None

@router.post("/waitlist/user/auth", response_model=APIResponse)
@handle_route_errors("authenticating")
async def authenticate_waitlist_viewer(
    request: PasswordRequest,
    response: Response,
    http_request: Request,
):
    """Authenticate with password to view waitlist."""
    if not settings.waitlist_admin.password:
        return success_response(
            data={"authenticated": False, "message": "Waitlist admin not configured"},
            success=False
        )
    
    retry_after = _rate_limit_auth(http_request)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return success_response(
            data={
                "authenticated": False,
                "message": "Too many attempts. Try again later.",
                "retry_after_seconds": retry_after,
            },
            success=False,
        )

    received_password = request.password.strip() if request.password else ""
    expected_password = settings.waitlist_admin.password.strip()
    
    if not hmac.compare_digest(received_password, expected_password):
        return success_response(
            data={"authenticated": False, "message": "Invalid password"},
            success=False
        )
    
    session_token = generate_session_token()
    
    env = os.getenv("ENVIRONMENT", "development").lower()
    forwarded_proto = http_request.headers.get("x-forwarded-proto", "").lower()
    is_secure = (env == "production") or (forwarded_proto == "https") or (http_request.url.scheme == "https")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=86400
    )
    
    return success_response(
        data={"authenticated": True, "message": "Authentication successful"}
    )

@router.get("/waitlist/user/entries", response_model=APIResponse)
@handle_route_errors("fetching waitlist entries")
async def get_waitlist_entries(
    request: Request,
    service: WaitlistService = Depends(get_waitlist_service),
    _: bool = Depends(require_waitlist_auth)
):
    """Get all waitlist entries. Requires authentication."""
    entries = service.get_all_entries()
    return success_response(data={"entries": entries, "total": len(entries)})

@router.post("/waitlist/user/logout", response_model=APIResponse)
async def logout_waitlist_viewer(response: Response):
    """Logout by clearing the session cookie."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    is_production = env == "production"
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=is_production,
        samesite="lax"
    )
    return success_response(data={"message": "Logged out successfully"})

# ------------------------------ END OF FILE ------------------------------