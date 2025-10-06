from fastapi import APIRouter, HTTPException, Header, Request
from typing import Dict, Any, Optional
import hmac, hashlib, json

from .service import PlaidService, PLAID_WEBHOOK_SECRET
from core.db.operations.plaid_operations import store_plaid_webhook_event

router = APIRouter(prefix="/plaid", tags=["plaid"])

# ------------------------------ HELPERS ------------------------------
def get_service() -> PlaidService:
    return PlaidService()

def ensure_fields(data: Dict[str, Any], fields: list[str]) -> None:
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {', '.join(missing)}")

def check_result(result: Dict[str, Any], error_msg: str) -> None:
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", error_msg))


# ------------------------------ ROUTES ------------------------------
@router.get("/link/token")
async def create_link_token(user_id: str):
    service = get_service()
    result = await service.create_link_token(user_id)
    check_result(result, "Failed to create link token")
    return result


@router.post("/token/exchange")
async def exchange_public_token(body: Dict[str, Any]):
    ensure_fields(body, ["public_token"])
    service = get_service()
    result = await service.exchange_public_token(body["public_token"])
    check_result(result, "Failed to exchange token")
    return result


@router.post("/accounts")
async def list_accounts(body: Dict[str, Any]):
    ensure_fields(body, ["access_token"])
    service = get_service()
    result = await service.get_accounts(body["access_token"])
    check_result(result, "Failed to fetch accounts")
    return result


@router.post("/transactions")
async def list_transactions(body: Dict[str, Any]):
    ensure_fields(body, ["access_token", "start_date", "end_date"])
    service = get_service()
    result = await service.get_transactions(
        body["access_token"], body["start_date"], body["end_date"]
    )
    check_result(result, "Failed to fetch transactions")
    return result


@router.get("/webhook/events")
async def webhook_events():
    return {"webhook_events": get_service().get_webhook_events()}


@router.post("/webhook/receive")
async def receive_webhook(
    request: Request,
    x_plaid_signature: Optional[str] = Header(None, alias="Plaid-Verification"),
):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if PLAID_WEBHOOK_SECRET:
        if not x_plaid_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        expected = hmac.new(
            PLAID_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(x_plaid_signature, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    webhook_type = payload.get("webhook_type", "unknown")
    webhook_code = payload.get("webhook_code", "unknown")

    try:
        event_id = store_plaid_webhook_event(
            None, webhook_type, webhook_code, payload, x_plaid_signature
        )
    except Exception:
        event_id = None

    return {
        "success": True,
        "webhook_type": webhook_type,
        "webhook_code": webhook_code,
        "event_id": event_id,
    }
