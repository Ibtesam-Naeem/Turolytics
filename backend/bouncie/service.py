# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, urlparse, parse_qs
from sqlalchemy.orm import Session

from .helpers import format_date_for_api
from .constants import (
    REQUEST_TIMEOUT_SECONDS,
    DEFAULT_TOKEN_EXPIRY_SECONDS,
    DEFAULT_DAYS_BACK,
    CONTENT_TYPE_JSON,
    USER_AGENT
)
from core.database.models import BouncieIntegration, Account
from core.database.db_service import DatabaseService

logger = logging.getLogger(__name__)

# ------------------------------ BOUNCIE CONFIGURATION ------------------------------

BOUNCIE_CLIENT_ID = os.getenv("BOUNCIE_CLIENT_ID")
BOUNCIE_CLIENT_SECRET = os.getenv("BOUNCIE_CLIENT_SECRET")
BOUNCIE_REDIRECT_URI = os.getenv("BOUNCIE_REDIRECT_URI", "http://localhost:8000/auth/bouncie/callback")
BOUNCIE_API_BASE = "https://api.bouncie.dev/v1"
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"
BOUNCIE_TOKEN_URL = "https://auth.bouncie.com/oauth/token"

# ------------------------------ BOUNCIE SERVICE ------------------------------

class BouncieService:
    def __init__(self, db: Session = None, account: Account = None, account_id: int = None, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        self.client_id = client_id or BOUNCIE_CLIENT_ID
        self.client_secret = client_secret or BOUNCIE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or BOUNCIE_REDIRECT_URI
        
        self.db = db
        
        if account:
            self.account = account
            self.account_id = account.id
        else:
            self.account = None
            self.account_id = account_id
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self._tokens_loaded = False
        self.headers = {"Content-Type": CONTENT_TYPE_JSON, "User-Agent": USER_AGENT}
        
        if self.db and self.account_id:
            self._load_tokens()

    # ------------------------------ TOKEN MANAGEMENT ------------------------------

    @staticmethod
    def _calculate_token_expiry(expires_in: int) -> datetime:
        """Calculate token expiry datetime from expires_in seconds."""
        return datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def _get_account(self, raise_on_error: bool = False) -> Optional[Account]:
        """Get account by account_id, trying both account_id and user_id lookup."""
        if not self.db or not self.account_id:
            return None
        
        account = DatabaseService.get_account(self.db, account_id=self.account_id)
        if not account:
            account = DatabaseService.get_account(self.db, user_id=self.account_id)
        
        if not account:
            if raise_on_error:
                all_accounts = self.db.query(Account).all()
                account_info = ', '.join(f"id={a.id}, user_id={a.user_id}, email={a.email}" for a in all_accounts) or 'None'
                raise ValueError(
                    f"Account {self.account_id} not found (tried as both account_id and user_id).\n"
                    f"Available accounts: {account_info}"
                )
            logger.warning(f"Account {self.account_id} not found (tried as both account_id and user_id)")
            return None
        
        self.account_id = account.id
        self.account = account
        return account

    @staticmethod
    def _extract_refresh_token(token_data: Dict[str, Any], existing_refresh_token: Optional[str] = None) -> Optional[str]:
        """Extract refresh token from token response, trying various field names."""
        return (
            token_data.get("refresh_token") or 
            token_data.get("refreshToken") or
            token_data.get("refresh") or
            existing_refresh_token
        )

    def _load_tokens(self):
        """Load tokens from database for the current account."""
        try:
            account = self._get_account()
            if not account:
                return

            integration = self.db.query(BouncieIntegration).filter(
                BouncieIntegration.account_id == account.id
            ).first()
            
            if integration:
                self.access_token = integration.access_token
                self.refresh_token = integration.refresh_token
                self.token_expires_at = integration.expires_at
                self.headers["Authorization"] = self.access_token
                logger.debug(f"Loaded Bouncie tokens for account {account.id} (user_id: {account.user_id})")
                if not self.refresh_token:
                    logger.debug(f"No refresh token found for account {account.id} - token refresh will not be possible")
            else:
                logger.debug(f"No Bouncie integration found for account {account.id} (user_id: {account.user_id})")
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
        finally:
            self._tokens_loaded = True

    def _save_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int):
        """Save or update tokens in the database."""
        try:
            account = self._get_account(raise_on_error=True)
            expires_at = self._calculate_token_expiry(expires_in)
            
            integration = self.db.query(BouncieIntegration).filter(
                BouncieIntegration.account_id == account.id
            ).first()
            
            if not integration:
                integration = BouncieIntegration(account_id=account.id)
                self.db.add(integration)
            
            integration.access_token = access_token
            if refresh_token is not None:
                integration.refresh_token = refresh_token
            integration.expires_at = expires_at
            
            self.db.commit()
            self.db.refresh(integration)
            
            self.access_token = access_token
            self.refresh_token = refresh_token if refresh_token is not None else self.refresh_token
            self.token_expires_at = expires_at
            self.headers["Authorization"] = self.access_token
            
            logger.info(f"Saved Bouncie tokens for account {account.id} (user_id: {account.user_id})")
            return True
            
        except ValueError as e:
            logger.error(f"Cannot save tokens: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving tokens: {e}", exc_info=True)
            self.db.rollback()
            return False

    def _refresh_access_token(self) -> bool:
        """Refresh the access token synchronously."""
        if not self.refresh_token:
            logger.warning("Cannot refresh token: No refresh token available")
            return False

        try:
            logger.info("Attempting to refresh access token using refresh token...")
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "redirect_uri": self.redirect_uri
            }

            response = requests.post(
                BOUNCIE_TOKEN_URL,
                json=data,
                headers={"Content-Type": CONTENT_TYPE_JSON},
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                token_data = response.json()
                logger.info("Token refresh successful")
                
                new_refresh_token = self._extract_refresh_token(token_data, self.refresh_token)
                
                self._save_tokens(
                    token_data.get("access_token"),
                    new_refresh_token, 
                    token_data.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS)
                )
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.exception("Exception refreshing token")
            return False
    
    # ------------------------------ AUTHENTICATION ------------------------------
    
    def get_authorization_url(self, state: str = None) -> str:
        params = {
            "response_type": "code", 
            "client_id": self.client_id, 
            "redirect_uri": self.redirect_uri, 
            "scope": "read offline_access"
        }
        if state:
            params["state"] = state
        
        return f"{BOUNCIE_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    def extract_code_from_callback_url(callback_url_or_code: str) -> str:
        if callback_url_or_code.startswith(('http://', 'https://')):
            parsed = urlparse(callback_url_or_code)
            query_params = parse_qs(parsed.query)
            code = query_params.get('code', [None])[0]
            if code:
                return code
            raise ValueError(f"No 'code' parameter found in callback URL: {callback_url_or_code}")
        
        return callback_url_or_code
    
    def _exchange_code_for_token_sync(self, authorization_code: str) -> Dict[str, Any]:
        """Synchronous helper for token exchange."""
        try:
            code = self.extract_code_from_callback_url(authorization_code)
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(
                BOUNCIE_TOKEN_URL, 
                json=data, 
                headers={"Content-Type": CONTENT_TYPE_JSON}, 
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                refresh_token = self._extract_refresh_token(token_data)
                expires_in = token_data.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS)
                
                if self.db and self.account_id:
                    save_success = self._save_tokens(
                        token_data.get("access_token"),
                        refresh_token,  
                        expires_in
                    )
                    if not save_success:
                        logger.warning("Token exchange succeeded but failed to save to database")
                else:
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = refresh_token
                    self.token_expires_at = self._calculate_token_expiry(expires_in)
                    self.headers["Authorization"] = self.access_token

                return {"success": True, "data": token_data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token asynchronously."""
        return await asyncio.to_thread(self._exchange_code_for_token_sync, authorization_code)
    
    # ------------------------------ CORE API METHODS ------------------------------
    
    def _ensure_valid_token(self) -> Optional[Dict[str, Any]]:
        """Ensure we have a valid access token, refreshing if necessary."""
        if self.db and self.account_id and not self._tokens_loaded:
            self._load_tokens()
        
        if not self.access_token:
            return {"success": False, "error": "No access token available"}
        
        if self.token_expires_at and datetime.now(timezone.utc) >= self.token_expires_at:
            if not self.refresh_token:
                logger.warning("Token expired but no refresh token available")
                return {"success": False, "error": "Token expired and no refresh token available. Please reconnect Bouncie."}
            if not self._refresh_access_token():
                logger.error("Token refresh failed")
                return {"success": False, "error": "Token expired and refresh failed. Please reconnect Bouncie."}
        
        return None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        token_error = self._ensure_valid_token()
        if token_error:
            return token_error
        
        try:
            url = f"{BOUNCIE_API_BASE}{endpoint}"
            headers = {**self.headers, **kwargs.get('headers', {})}
            request_kwargs = {k: v for k, v in kwargs.items() if k != 'headers'}
            
            def _do_request():
                return requests.request(method, url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS, **request_kwargs)
            
            logger.debug(f"Making {method} request to {endpoint}" + (f" with params: {params}" if params else ""))
            
            response = _do_request()
            
            if response.status_code == 401 and self.refresh_token:
                logger.info("Received 401, attempting token refresh and retry")
                if self._refresh_access_token():
                    headers["Authorization"] = self.headers["Authorization"]
                    response = _do_request()
                else:
                    logger.error("Token refresh failed after 401 error")
            
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
            
            if response.status_code == 200:
                logger.debug(f"Bouncie API {method} {endpoint} - Success")
                return {"success": True, "data": response_data, "status_code": response.status_code}
            else:
                logger.error(f"Bouncie API {method} {endpoint} - Failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "data": response_data,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.exception(f"Exception in _make_request: {e}")
            return {"success": False, "error": str(e)}
    
    async def _api_call(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(self._make_request, method, endpoint, params, **kwargs)
    
    async def get_vehicles(self) -> Dict[str, Any]:
        logger.debug("Fetching vehicles from Bouncie API")
        result = await self._api_call("GET", "/vehicles")
        if result.get("success"):
            logger.info(f"Retrieved {len(result.get('data', []))} vehicles from Bouncie")
        else:
            logger.error(f"Failed to fetch vehicles: {result.get('error')}")
        return result
    
    async def get_trips(
        self,
        gps_format: str = "geojson",
        start_date: str = None,
        end_date: str = None,
        imei: str = None
    ) -> Dict[str, Any]:
        if not start_date:
            start_date = format_date_for_api(datetime.now() - timedelta(days=DEFAULT_DAYS_BACK))
        if not end_date:
            end_date = format_date_for_api(datetime.now())
        params = {"gpsFormat": gps_format, "starts-after": start_date, "ends-before": end_date}
        if imei:
            params["imei"] = imei
        
        logger.debug(f"Fetching trips from Bouncie API (start={start_date}, end={end_date}, imei={imei})")
        result = await self._api_call("GET", "/trips", params=params)
        if result.get("success"):
            logger.info(f"Retrieved {len(result.get('data', []))} trips from Bouncie")
        else:
            logger.error(f"Failed to fetch trips: {result.get('error')}")
        return result
    
    # ------------------------------ WEBHOOK SUPPORT ------------------------------
    
    def get_webhook_events(self) -> List[str]:
        return [
            "device_connected", 
            "device_disconnected", 
            "new_trip_data", 
            "new_trip_metrics",
            "new_mil_event", 
            "new_battery_status", 
            "trip_ended", 
            "geo_zone_entered", 
            "geo_zone_exited",
            "vin_change"
        ]
    
# ------------------------------ END OF FILE ------------------------------
