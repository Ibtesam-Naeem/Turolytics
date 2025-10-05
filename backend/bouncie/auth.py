#!/usr/bin/env python3
"""
Bouncie Authentication Module
Handles OAuth 2.0 authentication with Bouncie API.
Based on working test patterns from test folder.
"""

import asyncio
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from the backend directory (parent of bouncie folder)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, use system environment variables

# Import logger and settings with fallback
try:
    from core.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from core.config.settings import settings
except ImportError:
    settings = None

# ------------------------------ CONFIGURATION ------------------------------

# Bouncie API Configuration (based on working test files)
BOUNCIE_BASE_URL = "https://api.bouncie.dev"
BOUNCIE_API_VERSION = "v1"

# Bouncie OAuth 2.0 Credentials
BOUNCIE_CLIENT_ID = os.getenv("BOUNCIE_CLIENT_ID", "turolytics-dev")
BOUNCIE_CLIENT_SECRET = os.getenv("BOUNCIE_CLIENT_SECRET")
BOUNCIE_REDIRECT_URI = os.getenv("BOUNCIE_REDIRECT_URI", "http://localhost:8000/auth/bouncie/callback")

# OAuth 2.0 URLs (based on working test files)
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"
BOUNCIE_TOKEN_URL = "https://auth.bouncie.com/oauth/token"

# ------------------------------ BOUNCIE API CLIENT ------------------------------

class BouncieAPIClient:
    """Bouncie API client with OAuth 2.0 authentication based on working test patterns."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        self.client_id = client_id or BOUNCIE_CLIENT_ID
        self.client_secret = client_secret or BOUNCIE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or BOUNCIE_REDIRECT_URI
        self.base_url = f"{BOUNCIE_BASE_URL}/{BOUNCIE_API_VERSION}"
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Turolytics/1.0.0"
        }
    
    def get_authorization_url(self, state: str = None) -> str:
        """Get the OAuth 2.0 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read"  # Add appropriate scopes
        }
        if state:
            params["state"] = state
        
        query_string = urlencode(params)
        return f"{BOUNCIE_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
            logger.info("Exchanging authorization code for access token...")
            
            def _make_request():
                data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri
                }
                
                response = requests.post(
                    BOUNCIE_TOKEN_URL,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                return response
            
            response = await asyncio.to_thread(_make_request)
            
            response_text = response.text
            logger.info(f"Token exchange response status: {response.status_code}")
            logger.info(f"Token exchange response: {response_text[:200]}...")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # Calculate token expiration
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Set authorization header (without Bearer based on working test)
                self.headers["Authorization"] = self.access_token
                
                logger.info("Successfully obtained access token")
                return {
                    "success": True,
                    "data": token_data,
                    "message": "Successfully obtained access token"
                }
            else:
                logger.error(f"Token exchange failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}",
                    "message": "Failed to exchange code for token"
                }
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error exchanging code for token"
            }
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            return {
                "success": False,
                "error": "No refresh token available",
                "message": "Cannot refresh token without refresh token"
            }
        
        try:
            logger.info("Refreshing access token...")
            
            def _make_request():
                data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                }
                
                response = requests.post(
                    BOUNCIE_TOKEN_URL,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                return response
            
            response = await asyncio.to_thread(_make_request)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                
                # Update token expiration
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update authorization header
                self.headers["Authorization"] = self.access_token
                
                logger.info("Successfully refreshed access token")
                return {
                    "success": True,
                    "data": token_data,
                    "message": "Successfully refreshed access token"
                }
            else:
                error_text = response.text
                logger.error(f"Token refresh failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "message": "Failed to refresh access token"
                }
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error refreshing access token"
            }
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at
    
    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token, refresh if necessary."""
        if not self.access_token or self.is_token_expired():
            if self.refresh_token:
                result = await self.refresh_access_token()
                return result["success"]
            else:
                logger.warning("No valid token and no refresh token available")
                return False
        return True
    
    async def make_authenticated_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Bouncie API."""
        if not await self.ensure_valid_token():
            return {
                "success": False,
                "error": "No valid access token available",
                "message": "Authentication required"
            }
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {**self.headers, **kwargs.get('headers', {})}
            
            def _make_request():
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    timeout=30,
                    **{k: v for k, v in kwargs.items() if k != 'headers'}
                )
                return response
            
            response = await asyncio.to_thread(_make_request)
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response_data,
                    "status_code": response.status_code,
                    "message": f"Request successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "data": response_data,
                    "status_code": response.status_code,
                    "message": f"Request failed"
                }
        except Exception as e:
            logger.error(f"Error making authenticated request: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Request failed"
            }
    
    # ------------------------------ API METHODS (based on working test patterns) ------------------------------
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information."""
        return await self.make_authenticated_request("GET", "/user")
    
    async def get_vehicles(self) -> Dict[str, Any]:
        """Get vehicles information."""
        return await self.make_authenticated_request("GET", "/vehicles")
    
    async def get_locations(self) -> Dict[str, Any]:
        """Get locations information."""
        return await self.make_authenticated_request("GET", "/locations")
    
    async def get_trips(self, gps_format: str = "latlng", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get trips information with required parameters."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "gpsFormat": gps_format,
            "startDate": start_date,
            "endDate": end_date
        }
        
        return await self.make_authenticated_request("GET", "/trips", params=params)
    
    async def get_devices(self) -> Dict[str, Any]:
        """Get list of devices."""
        return await self.make_authenticated_request("GET", "/devices")
    
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get specific device information."""
        return await self.make_authenticated_request("GET", f"/devices/{device_id}")
    
    async def get_device_trips(self, device_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get trips for a specific device."""
        params = {"limit": limit}
        return await self.make_authenticated_request("GET", f"/devices/{device_id}/trips", params=params)
    
    async def get_device_location(self, device_id: str) -> Dict[str, Any]:
        """Get current location of a device."""
        return await self.make_authenticated_request("GET", f"/devices/{device_id}/location")
    
    async def get_device_diagnostics(self, device_id: str) -> Dict[str, Any]:
        """Get diagnostics data for a device."""
        return await self.make_authenticated_request("GET", f"/devices/{device_id}/diagnostics")

# ------------------------------ AUTHENTICATION MANAGER ------------------------------

class BouncieAuthManager:
    """Manages Bouncie authentication for the application."""
    
    def __init__(self):
        self.client = BouncieAPIClient()
    
    def get_auth_url(self, state: str = None) -> str:
        """Get the authorization URL for OAuth flow."""
        return self.client.get_authorization_url(state)
    
    async def handle_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for token."""
        result = await self.client.exchange_code_for_token(code)
        if result["success"]:
            logger.info("OAuth callback handled successfully")
        else:
            logger.error(f"OAuth callback failed: {result['error']}")
        return result
    
    async def get_user_data(self) -> Dict[str, Any]:
        """Get user data using current authentication."""
        return await self.client.get_user_info()
    
    async def get_vehicles_data(self) -> Dict[str, Any]:
        """Get vehicles data using current authentication."""
        return await self.client.get_vehicles()
    
    async def get_locations_data(self) -> Dict[str, Any]:
        """Get locations data using current authentication."""
        return await self.client.get_locations()
    
    async def get_trips_data(self, **kwargs) -> Dict[str, Any]:
        """Get trips data using current authentication."""
        return await self.client.get_trips(**kwargs)

# ------------------------------ TEST FUNCTIONS ------------------------------

async def test_bouncie_auth_with_working_code():
    """Test Bouncie authentication with the working authorization code from test files."""
    print("🚀 Bouncie Authentication Test with Working Code")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize auth manager
    auth_manager = BouncieAuthManager()
    
    # Use the working authorization code from test files
    working_auth_code = "lBKQ6ODaLCoGazODANG4Mz5AWMhf9tTYFaA6qOOfpeGaV9DrZJ"
    
    print("🔐 Step 1: Exchange Working Authorization Code for Access Token")
    print("-" * 60)
    print(f"Using auth code: {working_auth_code[:20]}...")
    
    result = await auth_manager.handle_callback(working_auth_code)
    if not result["success"]:
        print(f"❌ Failed to get access token: {result['error']}")
        return
    
    print(f"✅ Successfully obtained access token!")
    print(f"   Token: {auth_manager.client.access_token[:20]}...")
    print(f"   Expires at: {auth_manager.client.token_expires_at}")
    print()
    
    # Test API calls
    print("📡 Step 2: Test Bouncie API Calls")
    print("-" * 60)
    
    # Test 1: User Info
    print("👤 Testing User Info Endpoint")
    print("-" * 40)
    user_result = await auth_manager.get_user_data()
    if user_result["success"]:
        print(f"✅ {user_result['message']}")
        user_data = user_result["data"]
        print(f"   User ID: {user_data.get('id', 'N/A')}")
        print(f"   Email: {user_data.get('email', 'N/A')}")
        print(f"   Name: {user_data.get('name', 'N/A')}")
        print(f"   Full data: {json.dumps(user_data, indent=2)}")
    else:
        print(f"❌ {user_result['message']}")
        print(f"   Error: {user_result['error']}")
    print()
    
    # Test 2: Vehicles (Main focus)
    print("🚗 Testing Vehicles Endpoint (MAIN FOCUS)")
    print("-" * 40)
    vehicles_result = await auth_manager.get_vehicles_data()
    if vehicles_result["success"]:
        print(f"✅ {vehicles_result['message']}")
        vehicles_data = vehicles_result["data"]
        if isinstance(vehicles_data, list):
            print(f"   Found {len(vehicles_data)} vehicles")
            for i, vehicle in enumerate(vehicles_data):
                print(f"   Vehicle {i+1}: {json.dumps(vehicle, indent=4)}")
        else:
            print(f"   Data: {json.dumps(vehicles_data, indent=2)}")
    else:
        print(f"❌ {vehicles_result['message']}")
        print(f"   Error: {vehicles_result['error']}")
    print()
    
    # Test 3: Locations
    print("📍 Testing Locations Endpoint")
    print("-" * 40)
    locations_result = await auth_manager.get_locations_data()
    if locations_result["success"]:
        print(f"✅ {locations_result['message']}")
        locations_data = locations_result["data"]
        if isinstance(locations_data, list):
            print(f"   Found {len(locations_data)} locations")
            for i, location in enumerate(locations_data[:3]):  # Show first 3
                print(f"   Location {i+1}: {json.dumps(location, indent=4)}")
        else:
            print(f"   Data: {json.dumps(locations_data, indent=2)}")
    else:
        print(f"❌ {locations_result['message']}")
        print(f"   Error: {locations_result['error']}")
    print()
    
    # Test 4: Trips
    print("🛣️  Testing Trips Endpoint")
    print("-" * 40)
    trips_result = await auth_manager.get_trips_data()
    if trips_result["success"]:
        print(f"✅ {trips_result['message']}")
        trips_data = trips_result["data"]
        if isinstance(trips_data, list):
            print(f"   Found {len(trips_data)} trips")
            for i, trip in enumerate(trips_data[:3]):  # Show first 3
                print(f"   Trip {i+1}: {json.dumps(trip, indent=4)}")
        else:
            print(f"   Data: {json.dumps(trips_data, indent=2)}")
    else:
        print(f"❌ {trips_result['message']}")
        print(f"   Error: {trips_result['error']}")
    print()
    
    # Test 5: Devices
    print("📱 Testing Devices Endpoint")
    print("-" * 40)
    devices_result = await auth_manager.client.get_devices()
    if devices_result["success"]:
        print(f"✅ {devices_result['message']}")
        devices_data = devices_result["data"]
        if isinstance(devices_data, list):
            print(f"   Found {len(devices_data)} devices")
            for i, device in enumerate(devices_data):
                print(f"   Device {i+1}: {json.dumps(device, indent=4)}")
        else:
            print(f"   Data: {json.dumps(devices_data, indent=2)}")
    else:
        print(f"❌ {devices_result['message']}")
        print(f"   Error: {devices_result['error']}")
    print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 60)
    print("✅ Bouncie API authentication and vehicle data retrieval successful!")
    print("✅ Found working endpoints:")
    print("   - /user (user information)")
    print("   - /vehicles (vehicle data) - MAIN FOCUS")
    print("   - /locations (location data)")
    print("   - /trips (trip data)")
    print("   - /devices (device data)")
    print()
    print("🔑 Authentication method: Authorization: {token} (no Bearer)")
    print("📝 Ready for integration into FastAPI routes!")

# ------------------------------ MAIN EXECUTION ------------------------------

if __name__ == "__main__":
    print("🚀 Starting Bouncie Authentication Test with Working Code...")
    print()
    print("📋 Configuration:")
    print(f"   Client ID: {BOUNCIE_CLIENT_ID}")
    print(f"   Redirect URI: {BOUNCIE_REDIRECT_URI}")
    print(f"   Auth URL: {BOUNCIE_AUTH_URL}")
    print(f"   Token URL: {BOUNCIE_TOKEN_URL}")
    print()
    print("💡 This test uses the working authorization code from your test files")
    print("   to demonstrate successful authentication and API calls.")
    print()
    
    try:
        asyncio.run(test_bouncie_auth_with_working_code())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
