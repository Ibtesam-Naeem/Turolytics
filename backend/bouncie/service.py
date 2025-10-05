#!/usr/bin/env python3
"""
Bouncie Service
Complete Bouncie API implementation with webhook support.
"""

import asyncio
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

# Bouncie API Configuration
BOUNCIE_CLIENT_ID = os.getenv("BOUNCIE_CLIENT_ID", "turolytics-dev")
BOUNCIE_CLIENT_SECRET = os.getenv("BOUNCIE_CLIENT_SECRET")
BOUNCIE_REDIRECT_URI = os.getenv("BOUNCIE_REDIRECT_URI", "http://localhost:8000/auth/bouncie/callback")
BOUNCIE_API_BASE = "https://api.bouncie.dev/v1"
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"
BOUNCIE_TOKEN_URL = "https://auth.bouncie.com/oauth/token"

class BouncieService:
    """Complete Bouncie API service with webhook support."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        self.client_id = client_id or BOUNCIE_CLIENT_ID
        self.client_secret = client_secret or BOUNCIE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or BOUNCIE_REDIRECT_URI
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Turolytics/1.0.0"
        }
    
    def get_authorization_url(self, state: str = None) -> str:
        """Get OAuth 2.0 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read"
        }
        if state:
            params["state"] = state
        
        query_string = urlencode(params)
        return f"{BOUNCIE_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
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
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Set authorization header (without Bearer based on working tests)
                self.headers["Authorization"] = self.access_token
                
                return {
                    "success": True,
                    "data": token_data,
                    "message": "Successfully obtained access token"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to exchange code for token"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error exchanging code for token"
            }
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Bouncie API."""
        if not self.access_token:
            return {
                "success": False,
                "error": "No access token available",
                "message": "Authentication required"
            }
        
        try:
            url = f"{BOUNCIE_API_BASE}{endpoint}"
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
                    "message": "Request successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "data": response_data,
                    "status_code": response.status_code,
                    "message": "Request failed"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Request failed"
            }
    
    # ------------------------------ CORE API ENDPOINTS ------------------------------
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information."""
        return await self.make_request("GET", "/user")
    
    async def get_vehicles(self) -> Dict[str, Any]:
        """Get vehicles information."""
        return await self.make_request("GET", "/vehicles")
    
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
        
        return await self.make_request("GET", "/trips", params=params)
    
    # ------------------------------ WEBHOOK SUPPORT ------------------------------
    
    def get_webhook_events(self) -> List[str]:
        """Get list of available webhook events."""
        return [
            "device_connected",
            "device_disconnected", 
            "new_trip_data",
            "new_trip_metrics",
            "new_mil_event",
            "new_battery_status",
            "trip_ended",
            "geo_zone_entered",
            "geo_zone_exited"
        ]
    
    def create_webhook_payload(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook payload structure."""
        return {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "source": "bouncie_api"
        }
    
    def validate_webhook_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate incoming webhook payload."""
        required_fields = ["event", "timestamp", "data"]
        return all(field in payload for field in required_fields)
    
    # ------------------------------ VEHICLE ANALYTICS ------------------------------
    
    async def get_vehicle_analytics(self, vehicle_imei: str) -> Dict[str, Any]:
        """Get comprehensive vehicle analytics."""
        analytics = {
            "vehicle_info": None,
            "current_status": None,
            "recent_trips": None,
            "health_status": None
        }
        
        # Get vehicle info from vehicles endpoint
        vehicles_result = await self.get_vehicles()
        if vehicles_result["success"]:
            vehicles = vehicles_result["data"]
            if isinstance(vehicles, list):
                for vehicle in vehicles:
                    if vehicle.get("imei") == vehicle_imei:
                        analytics["vehicle_info"] = {
                            "make": vehicle.get("model", {}).get("make"),
                            "model": vehicle.get("model", {}).get("name"),
                            "year": vehicle.get("model", {}).get("year"),
                            "vin": vehicle.get("vin"),
                            "nickname": vehicle.get("nickName")
                        }
                        
                        stats = vehicle.get("stats", {})
                        analytics["current_status"] = {
                            "location": stats.get("location"),
                            "odometer": stats.get("odometer"),
                            "fuel_level": stats.get("fuelLevel"),
                            "is_running": stats.get("isRunning"),
                            "speed": stats.get("speed"),
                            "last_updated": stats.get("lastUpdated"),
                            "battery": stats.get("battery"),
                            "mil": stats.get("mil")
                        }
                        break
        
        # Get recent trips
        trips_result = await self.get_trips()
        if trips_result["success"]:
            analytics["recent_trips"] = trips_result["data"]
        
        return analytics

# ------------------------------ CONVENIENCE FUNCTIONS ------------------------------

async def get_bouncie_vehicle_data(authorization_code: str) -> Dict[str, Any]:
    """Convenience function to get vehicle data with authorization code."""
    service = BouncieService()
    
    # Authenticate
    auth_result = await service.exchange_code_for_token(authorization_code)
    if not auth_result["success"]:
        return auth_result
    
    # Get vehicle data
    vehicles_result = await service.get_vehicles()
    if not vehicles_result["success"]:
        return vehicles_result
    
    return {
        "success": True,
        "vehicles": vehicles_result["data"],
        "user": await service.get_user_info(),
        "webhook_events": service.get_webhook_events()
    }

# ------------------------------ MAIN EXECUTION (for testing) ------------------------------

if __name__ == "__main__":
    print("🚀 Bouncie Service - Test Mode")
    print("=" * 40)
    print("This is the Bouncie service module.")
    print("Use get_bouncie_vehicle_data(auth_code) to get vehicle data.")
    print()
    print("Available webhook events:")
    service = BouncieService()
    for event in service.get_webhook_events():
        print(f"  - {event}")