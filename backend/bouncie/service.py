# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .helpers import format_date_for_api
from core.database.models import BouncieIntegration, Account
from core.database.db_service import DatabaseService

load_dotenv()

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
        
        # Support both Account object and account_id for backward compatibility
        if account:
            self.account = account
            self.account_id = account.id
        elif account_id:
            self.account_id = account_id
            self.account = None
        else:
            self.account = None
            self.account_id = None
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.headers = {"Content-Type": "application/json", "User-Agent": "BouncieAPI/1.0.0"}
        
        if self.db and self.account_id:
            self._load_tokens()

    # ------------------------------ TOKEN MANAGEMENT ------------------------------

    def _load_tokens(self):
        """Load tokens from database for the current account."""
        if not self.db or not self.account_id:
            return

        try:
            account = self.db.query(Account).filter(Account.id == self.account_id).first()
            
            if not account:
                account = DatabaseService.get_account_by_user_id(self.db, self.account_id)
            
            if not account:
                logger.warning(f"Account {self.account_id} not found")
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
                if self.refresh_token:
                    logger.debug(f"✅ Refresh token loaded: {self.refresh_token[:10]}...")
                else:
                    logger.warning(f"⚠️  No refresh token found for account {account.id} - token refresh will not be possible. Please re-authenticate with offline_access scope.")
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")

    def _save_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int):
        """Save or update tokens in the database."""
        if not self.db or not self.account_id:
            logger.warning("Cannot save tokens: No DB session or account_id provided")
            return False

        try:
            account = self.db.query(Account).filter(Account.id == self.account_id).first()
            
            if not account:
                account = DatabaseService.get_account_by_user_id(self.db, self.account_id)
            
            if not account:
                all_accounts = self.db.query(Account).all()
                account_info = [f"id={a.id}, user_id={a.user_id}, email={a.email}" for a in all_accounts]
                logger.error(
                    f"Account {self.account_id} not found - cannot save tokens.\n"
                    f"Available accounts: {', '.join(account_info) if account_info else 'None'}\n"
                    f"Please ensure the account exists in the database."
                )
                return False
            
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            integration = self.db.query(BouncieIntegration).filter(
                BouncieIntegration.account_id == account.id
            ).first()
            
            if not integration:
                integration = BouncieIntegration(account_id=account.id)
                self.db.add(integration)
            
            integration.access_token = access_token
            # Always update refresh_token if provided, otherwise preserve existing
            if refresh_token:
                integration.refresh_token = refresh_token
            # If refresh_token is None and we don't have one, keep existing (don't overwrite with None)
            elif not integration.refresh_token:
                # Only set to None if integration is new and we have no refresh_token
                pass  # Keep it as None for new integrations
            integration.expires_at = expires_at
            
            self.db.commit()
            self.db.refresh(integration)
            
            self.access_token = access_token
            if refresh_token:
                self.refresh_token = refresh_token
            self.token_expires_at = expires_at
            self.headers["Authorization"] = self.access_token
            
            logger.info(f"Saved Bouncie tokens for account {account.id} (user_id: {account.user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tokens: {e}", exc_info=True)
            self.db.rollback()
            return False

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token (Async wrapper)."""
        return await asyncio.to_thread(self._refresh_access_token_sync)

    def _refresh_access_token_sync(self) -> bool:
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
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                logger.info(f"✅ Token refresh successful")
                
                # Preserve existing refresh_token if new one is not provided
                new_refresh_token = (
                    token_data.get("refresh_token") or 
                    token_data.get("refreshToken") or
                    token_data.get("refresh") or
                    self.refresh_token  # Keep existing if not provided
                )
                
                if new_refresh_token != self.refresh_token:
                    logger.info(f"New refresh token received: {new_refresh_token[:20]}...")
                else:
                    logger.info("Using existing refresh token (no new one provided)")
                
                self._save_tokens(
                    token_data.get("access_token"),
                    new_refresh_token, 
                    token_data.get("expires_in", 3600)
                )
                logger.info("✅ Tokens saved successfully after refresh")
                return True
            else:
                logger.error(f"❌ Token refresh failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Exception refreshing token: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # ------------------------------ AUTHENTICATION ------------------------------
    
    def get_authorization_url(self, state: str = None) -> str:
        # Include offline_access scope to request refresh tokens
        params = {
            "response_type": "code", 
            "client_id": self.client_id, 
            "redirect_uri": self.redirect_uri, 
            "scope": "read offline_access"
        }
        if state:
            params["state"] = state
        logger.info(f"Generated OAuth URL with scope: {params.get('scope')}")
        return f"{BOUNCIE_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    def extract_code_from_callback_url(callback_url_or_code: str) -> str:
        if callback_url_or_code.startswith('http://') or callback_url_or_code.startswith('https://'):
            parsed = urlparse(callback_url_or_code)
            query_params = parse_qs(parsed.query)
            code = query_params.get('code', [None])[0]
            if code:
                return code
            raise ValueError(f"No 'code' parameter found in callback URL: {callback_url_or_code}")
        
        return callback_url_or_code
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        try:
            code = self.extract_code_from_callback_url(authorization_code)
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(BOUNCIE_TOKEN_URL, json=data, 
                                   headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 401:
                response = requests.post(BOUNCIE_TOKEN_URL, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Detailed logging to see exactly what Bouncie returns
                import json
                logger.info("=" * 80)
                logger.info("BOUNCIE TOKEN EXCHANGE RESPONSE:")
                logger.info(json.dumps(token_data, indent=2))
                logger.info("=" * 80)
                logger.info(f"Response keys: {list(token_data.keys())}")
                logger.info(f"Has access_token: {'access_token' in token_data}")
                logger.info(f"Has refresh_token: {'refresh_token' in token_data}")
                
                # Check for refresh token in various possible field names
                refresh_token = (
                    token_data.get("refresh_token") or 
                    token_data.get("refreshToken") or
                    token_data.get("refresh") or
                    None
                )
                
                if refresh_token:
                    logger.info(f"✅ Refresh token found: {refresh_token[:20]}...")
                else:
                    logger.warning("⚠️  No refresh token found in response")
                    logger.warning(f"Available keys: {list(token_data.keys())}")
                    logger.warning("This may be because 'offline_access' scope was not included in the authorization request.")
                
                if self.db and self.account_id:
                    save_success = self._save_tokens(
                        token_data.get("access_token"),
                        refresh_token,  
                        token_data.get("expires_in", 3600)
                    )
                    if not save_success:
                        logger.warning("Token exchange succeeded but failed to save to database")
                    elif refresh_token:
                        logger.info(f"✅ Refresh token saved successfully to database - automatic refresh is now enabled")
                    else:
                        logger.warning("⚠️  No refresh_token in token response - token refresh will not be possible")
                        logger.warning("Please re-authenticate with 'offline_access' scope to enable automatic token refresh")
                else:
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = token_data.get("refresh_token")
                    self.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
                    self.headers["Authorization"] = self.access_token

                return {"success": True, "data": token_data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ------------------------------ CORE API METHODS ------------------------------
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # Always reload tokens from database to ensure we have the latest refresh_token
        if self.db and self.account_id:
            self._load_tokens()
        
        if not self.access_token:
            return {"success": False, "error": "No access token available"}
        
        # Check if token is expired and refresh automatically if we have a refresh token
        if self.token_expires_at and datetime.now(timezone.utc) >= self.token_expires_at:
             logger.info("⏰ Token expired, attempting automatic refresh...")
             if not self.refresh_token:
                 logger.warning("❌ Cannot refresh token: No refresh token available. Please reconnect Bouncie with offline_access scope.")
                 return {"success": False, "error": "Token expired and no refresh token available. Please reconnect Bouncie."}
             logger.info("🔄 Refreshing access token using refresh token...")
             if not self._refresh_access_token_sync():
                 logger.error("❌ Token refresh failed")
                 return {"success": False, "error": "Token expired and refresh failed. Please reconnect Bouncie."}
             logger.info("✅ Token refreshed successfully, continuing with request...")

        if not self.access_token:
            return {"success": False, "error": "No access token available"}
        
        try:
            url = f"{BOUNCIE_API_BASE}{endpoint}"
            headers = {**self.headers, **kwargs.get('headers', {})}
            
            request_kwargs = {k: v for k, v in kwargs.items() if k != 'headers'}
            if params:
                if method.upper() == "GET":
                    url += "?" + urlencode(params)
                    logger.debug(f"Making GET request to: {url}")
                else:
                    request_kwargs['params'] = params
            
            response = requests.request(method, url, headers=headers, timeout=30, **request_kwargs)
            
            # If we get 401, try refreshing the token automatically
            if response.status_code == 401 and self.refresh_token:
                logger.info("🔄 Received 401 Unauthorized, attempting automatic token refresh...")
                if self._refresh_access_token_sync():
                    # Reload tokens after refresh
                    self._load_tokens()
                    headers["Authorization"] = self.headers["Authorization"]
                    logger.info("✅ Token refreshed, retrying request...")
                    response = requests.request(method, url, headers=headers, timeout=30, **request_kwargs)
                else:
                    logger.error("❌ Token refresh failed after 401 error")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Log API responses for debugging
            if response.status_code == 200:
                logger.info(f"✅ Bouncie API {method} {endpoint} - Success")
                logger.debug(f"Response data type: {type(response_data)}")
                if isinstance(response_data, list):
                    logger.info(f"Response contains {len(response_data)} items")
                    if len(response_data) > 0:
                        logger.info(f"First item keys: {list(response_data[0].keys()) if isinstance(response_data[0], dict) else 'Not a dict'}")
                        logger.debug(f"First item sample: {str(response_data[0])[:500]}")
                elif isinstance(response_data, dict):
                    logger.info(f"Response keys: {list(response_data.keys())}")
                    logger.debug(f"Response sample: {str(response_data)[:500]}")
                else:
                    logger.debug(f"Response: {str(response_data)[:500]}")
                return {"success": True, "data": response_data, "status_code": response.status_code}
            else:
                logger.error(f"❌ Bouncie API {method} {endpoint} - Failed: {response.status_code}")
                logger.error(f"Response: {response_data}")
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
        logger.info("🚗 Fetching vehicles from Bouncie API...")
        result = await self._api_call("GET", "/vehicles")
        if result.get("success"):
            vehicles = result.get("data", [])
            logger.info(f"✅ Retrieved {len(vehicles)} vehicles from Bouncie")
            for i, vehicle in enumerate(vehicles[:3]):  # Log first 3 vehicles
                logger.info(f"  Vehicle {i+1}: IMEI={vehicle.get('imei')}, Keys={list(vehicle.keys()) if isinstance(vehicle, dict) else 'N/A'}")
                if isinstance(vehicle, dict) and 'location' in vehicle:
                    logger.info(f"    Location: {vehicle.get('location')}")
        else:
            logger.error(f"❌ Failed to fetch vehicles: {result.get('error')}")
        return result
    
    async def get_trips(
        self,
        gps_format: str = "geojson",
        start_date: str = None,
        end_date: str = None,
        imei: str = None
    ) -> Dict[str, Any]:
        if not start_date:
            start_date = format_date_for_api(datetime.now() - timedelta(days=30))
        if not end_date:
            end_date = format_date_for_api(datetime.now())
        params = {"gpsFormat": gps_format, "starts-after": start_date, "ends-before": end_date}
        if imei:
            params["imei"] = imei
        
        logger.info(f"🗺️  Fetching trips from Bouncie API (start={start_date}, end={end_date}, imei={imei})...")
        result = await self._api_call("GET", "/trips", params=params)
        if result.get("success"):
            trips = result.get("data", [])
            logger.info(f"✅ Retrieved {len(trips)} trips from Bouncie")
            for i, trip in enumerate(trips[:3]):  # Log first 3 trips
                logger.info(f"  Trip {i+1}: IMEI={trip.get('imei')}, Keys={list(trip.keys()) if isinstance(trip, dict) else 'N/A'}")
                if isinstance(trip, dict):
                    if 'gps' in trip:
                        gps_data = trip.get('gps')
                        logger.info(f"    GPS data type: {type(gps_data)}")
                        if isinstance(gps_data, dict) and 'coordinates' in gps_data:
                            coords = gps_data.get('coordinates')
                            logger.info(f"    GPS coordinates type: {type(coords)}, length: {len(coords) if isinstance(coords, (list, str)) else 'N/A'}")
                    if 'location' in trip:
                        logger.info(f"    Location: {trip.get('location')}")
        else:
            logger.error(f"❌ Failed to fetch trips: {result.get('error')}")
        return result
    
    async def get_vehicle_status(self, imei: str) -> Dict[str, Any]:
        """
        Get live status for a specific vehicle by IMEI.
        Returns current location, speed, fuel level, etc.
        """
        logger.info(f"🚗 Fetching vehicle status for IMEI: {imei}")
        result = await self._api_call("GET", f"/vehicles/{imei}")
        if result.get("success"):
            vehicle_data = result.get("data", {})
            logger.info(f"✅ Retrieved vehicle status for {imei}")
            if isinstance(vehicle_data, dict):
                logger.info(f"  Available keys: {list(vehicle_data.keys())}")
                if 'location' in vehicle_data:
                    logger.info(f"  Location: {vehicle_data.get('location')}")
        else:
            logger.error(f"❌ Failed to fetch vehicle status: {result.get('error')}")
        return result
    
    # ------------------------------ WEBHOOK SUPPORT ------------------------------
    
    def get_webhook_events(self) -> list:
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
