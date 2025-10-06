import os
import json
import asyncio
from typing import Dict, Any, Optional

import requests


# ------------------------------ CONFIG ------------------------------
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "").strip()
PLAID_SECRET = os.getenv("PLAID_SECRET", "").strip()
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").strip()  # sandbox | development | production
PLAID_WEBHOOK_SECRET = os.getenv("PLAID_WEBHOOK_SECRET", "").strip()

_BASE_URLS = {
    "production": "https://production.plaid.com",
    "development": "https://development.plaid.com",
    "sandbox": "https://sandbox.plaid.com",
}


# ------------------------------ SERVICE CLASS ------------------------------
class PlaidService:
    """Lightweight Plaid API wrapper for Turolytics."""

    def __init__(self, client_id: Optional[str] = None, secret: Optional[str] = None, env: Optional[str] = None):
        self.client_id = client_id or PLAID_CLIENT_ID
        self.secret = secret or PLAID_SECRET
        self.env = env or PLAID_ENV
        self.base_url = _BASE_URLS.get(self.env, _BASE_URLS["sandbox"])
        self.headers = {"Content-Type": "application/json"}

    def _auth(self) -> Dict[str, Any]:
        return {"client_id": self.client_id, "secret": self.secret}

    async def _post(self, endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Unified async POST helper."""
        def _req():
            return requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json={**self._auth(), **body},
                timeout=30,
            )
        resp = await asyncio.to_thread(_req)
        if resp.ok:
            return {"success": True, "data": resp.json()}
        return {"success": False, "status_code": resp.status_code, "error": resp.text}

    # ------------------------------ API METHODS ------------------------------
    async def create_link_token(self, user_id: str) -> Dict[str, Any]:
        return await self._post("/link/token/create", {
            "client_name": "Turolytics",
            "user": {"client_user_id": user_id},
            "products": ["transactions"],
            "country_codes": ["US"],
            "language": "en",
        })

    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        return await self._post("/item/public_token/exchange", {"public_token": public_token})

    async def get_accounts(self, access_token: str) -> Dict[str, Any]:
        return await self._post("/accounts/get", {"access_token": access_token})

    async def get_transactions(self, access_token: str, start_date: str, end_date: str) -> Dict[str, Any]:
        return await self._post("/transactions/get", {
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
            "options": {"count": 100, "offset": 0},
        })

    def get_webhook_events(self) -> Dict[str, Any]:
        return {
            "transactions": [
                "TRANSACTIONS_REMOVED",
                "DEFAULT_UPDATE",
                "INITIAL_UPDATE",
                "HISTORICAL_UPDATE",
            ]
        }
