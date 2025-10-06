# ------------------------------ IMPORTS ------------------------------
import asyncio
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from core.db.operations.bouncie_operations import save_bouncie_trips, save_bouncie_snapshot, get_bouncie_trips, get_bouncie_trip_stats

# ------------------------------ BOUNCIE CONFIGURATION ------------------------------

BOUNCIE_CLIENT_ID = os.getenv("BOUNCIE_CLIENT_ID")
BOUNCIE_CLIENT_SECRET = os.getenv("BOUNCIE_CLIENT_SECRET")
BOUNCIE_REDIRECT_URI = os.getenv("BOUNCIE_REDIRECT_URI")

BOUNCIE_API_BASE = "https://api.bouncie.dev/v1"
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"
BOUNCIE_TOKEN_URL = "https://auth.bouncie.com/oauth/token"

# ------------------------------ BOUNCIE SERVICE ------------------------------

class BouncieService:
    """Complete Bouncie API service with webhook support."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        self.client_id = client_id or BOUNCIE_CLIENT_ID
        self.client_secret = client_secret or BOUNCIE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or BOUNCIE_REDIRECT_URI
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.headers = {"Content-Type": "application/json", "User-Agent": "BouncieAPI/1.0.0"}
    
    # ------------------------------ AUTHENTICATION ------------------------------
    
    def get_authorization_url(self, state: str = None) -> str:
        """Get OAuth 2.0 authorization URL."""
        params = {"response_type": "code", "client_id": self.client_id, "redirect_uri": self.redirect_uri, "scope": "read"}
        if state:
            params["state"] = state
        return f"{BOUNCIE_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(BOUNCIE_TOKEN_URL, json=data, 
                                   headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
                self.headers["Authorization"] = self.access_token
                return {"success": True, "data": token_data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ------------------------------ CORE API METHODS ------------------------------
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]: 
        """Make authenticated request to Bouncie API."""
        if not self.access_token:
            return {"success": False, "error": "No access token available", "message": "Authentication required"}
        
        try:
            url = f"{BOUNCIE_API_BASE}{endpoint}"
            headers = {**self.headers, **kwargs.get('headers', {})}
            response = requests.request(method, url, headers=headers, timeout=30, 
                                      **{k: v for k, v in kwargs.items() if k != 'headers'})
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            if response.status_code == 200:
                return {"success": True, "data": response_data, "status_code": response.status_code, "message": "Request successful"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "data": response_data, 
                       "status_code": response.status_code, "message": "Request failed"}
        except Exception as e:
            return {"success": False, "error": str(e), "message": "Request failed"}
    
    async def _api_call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async API call."""
        return await asyncio.to_thread(self._make_request, method, endpoint, **kwargs)
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information."""
        return await self._api_call("GET", "/user")
    
    async def get_vehicles(self) -> Dict[str, Any]:
        """Get vehicles information."""
        return await self._api_call("GET", "/vehicles")
    
    async def get_trips(self, gps_format: str = "geojson", start_date: str = None, end_date: str = None, imei: str = None) -> Dict[str, Any]:
        """Get trips information with required parameters."""
        start_date = start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        params = {"gpsFormat": gps_format, "starts-after": start_date, "ends-before": end_date}
        if imei:
            params["imei"] = imei
        return await self._api_call("GET", "/trips", params=params)
    
    async def get_vehicle_by_imei(self, imei: str) -> Dict[str, Any]:
        """Get specific vehicle by IMEI."""
        return await self._api_call("GET", "/vehicles", params={"imei": imei})
    
    # ------------------------------ DATA PROCESSING ------------------------------
    
    def _process_vehicle_data(self, vehicle: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw vehicle data into structured format."""
        if not vehicle:
            return {"success": False, "error": "Vehicle not found", "message": "No vehicle data available"}
        
        stats = vehicle.get("stats", {})
        location = stats.get("location", {})
        mil = stats.get("mil", {})
        battery = mil.get("battery", {})
        
        return {
            "success": True,
            "data": {
                "vehicle_info": {
                    "imei": vehicle.get("imei"),
                    "nickname": vehicle.get("nickName"),
                    "vin": vehicle.get("vin"),
                    "make": vehicle.get("model", {}).get("make"),
                    "model": vehicle.get("model", {}).get("name"),
                    "year": vehicle.get("model", {}).get("year"),
                    "engine": vehicle.get("standardEngine")
                },
                "current_status": {
                    "odometer": stats.get("odometer"),
                    "fuel_level": stats.get("fuelLevel"),
                    "is_running": stats.get("isRunning"),
                    "speed": stats.get("speed"),
                    "last_updated": stats.get("lastUpdated"),
                    "timezone": stats.get("localTimeZone")
                },
                "location": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lon"),
                    "heading": location.get("heading"),
                    "address": location.get("address")
                },
                "health": {
                    "check_engine_on": mil.get("milOn"),
                    "battery_status": battery.get("status"),
                    "dtc_codes": mil.get("qualifiedDtcList", [])
                }
            }
        }
    
    def _process_trip_data(self, trips: list) -> Dict[str, Any]:
        """Process trip data and calculate statistics."""
        if not trips:
            return {"total_trips": 0, "total_distance": 0, "total_fuel": 0, "avg_speed": 0, "max_speed": 0}
        
        total_distance = sum(trip.get('distance', 0) for trip in trips)
        total_fuel = sum(trip.get('fuelConsumed', 0) for trip in trips)
        avg_speed = sum(trip.get('averageSpeed', 0) for trip in trips) / len(trips)
        max_speed = max(trip.get('maxSpeed', 0) for trip in trips)
        
        return {
            "total_trips": len(trips),
            "total_distance": total_distance,
            "total_fuel": total_fuel,
            "avg_speed": avg_speed,
            "max_speed": max_speed
        }
    
    # ------------------------------ CONVENIENCE METHODS ------------------------------
    
    async def get_current_vehicle_status(self, imei: str = None) -> Dict[str, Any]:
        """Get current status of a vehicle."""
        result = await self.get_vehicle_by_imei(imei) if imei else await self.get_vehicles()
        if not result["success"]:
            return result
        
        vehicles = result["data"]
        if not isinstance(vehicles, list) or not vehicles:
            return {"success": False, "error": "No vehicles found", "message": "No vehicles available"}
        
        return self._process_vehicle_data(vehicles[0])
    
    async def get_recent_trips(self, days: int = 7, imei: str = None) -> Dict[str, Any]:
        """Get recent trips for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return await self.get_trips("geojson", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), imei)
    
    async def get_vehicle_analytics(self, imei: str = None) -> Dict[str, Any]:
        """Get comprehensive vehicle analytics."""
        analytics = {"vehicle_info": None, "current_status": None, "recent_trips": None}
        
        status_result = await self.get_current_vehicle_status(imei)
        if status_result["success"]:
            analytics["vehicle_info"] = status_result["data"]["vehicle_info"]
            analytics["current_status"] = status_result["data"]["current_status"]
        
        trips_result = await self.get_recent_trips(7, imei)
        if trips_result["success"]:
            analytics["recent_trips"] = trips_result["data"]
        
        return analytics
    
    # ------------------------------ WEBHOOK SUPPORT ------------------------------
    
    def get_webhook_events(self) -> list:
        """Get list of available webhook events."""
        return [
            "device_connected", "device_disconnected", "new_trip_data", "new_trip_metrics",
            "new_mil_event", "new_battery_status", "trip_ended", "geo_zone_entered", "geo_zone_exited"
        ]
    
    def create_webhook_payload(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook payload structure."""
        return {"event": event_type, "timestamp": datetime.now().isoformat(), "data": data, "source": "bouncie_api"}
    
    def validate_webhook_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate incoming webhook payload."""
        required_fields = ["event", "timestamp", "data"]
        return all(field in payload for field in required_fields)
    
    # ------------------------------ DATABASE INTEGRATION ------------------------------
    
    async def save_vehicles_to_db(self, account_email: str) -> Dict[str, Any]:
        """Get vehicles from API and save to database."""
        try:
            vehicles_result = await self.get_vehicles()
            if not vehicles_result["success"]:
                return vehicles_result
            vehicles = vehicles_result["data"]
            if not isinstance(vehicles, list):
                return {"success": False, "error": "Invalid vehicles data format"}
            result = save_bouncie_snapshot(account_email, vehicles)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def save_trips_to_db(self, account_email: str, gps_format: str = "geojson", start_date: str = None, end_date: str = None, imei: str = None) -> Dict[str, Any]:
        """Get trips from API and save to database."""
        try:
            trips_result = await self.get_trips(gps_format, start_date, end_date, imei)
            if not trips_result["success"]:
                return trips_result
            trips = trips_result["data"]
            if not isinstance(trips, list):
                return {"success": False, "error": "Invalid trips data format"}
            result = save_bouncie_trips(account_email, trips)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_trips_from_db(self, account_email: str, imei: str = None, limit: int = 100) -> Dict[str, Any]:
        """Get trips from database."""
        try:
            trips = get_bouncie_trips(account_email, imei, limit)
            return {"success": True, "data": trips}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_trip_stats_from_db(self, account_email: str, imei: str = None, days: int = 30) -> Dict[str, Any]:
        """Get trip statistics from database."""
        try:
            stats = get_bouncie_trip_stats(account_email, imei, days)
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}

# ------------------------------ CONVENIENCE FUNCTIONS ------------------------------

async def get_bouncie_vehicle_data(authorization_code: str) -> Dict[str, Any]:
    """Convenience function to get vehicle data with authorization code."""
    service = BouncieService()
    
    auth_result = await service.exchange_code_for_token(authorization_code)
    if not auth_result["success"]:
        return auth_result
    
    vehicles_result = await service.get_vehicles()
    if not vehicles_result["success"]:
        return vehicles_result
    
    return {
        "success": True,
        "vehicles": vehicles_result["data"],
        "user": await service.get_user_info(),
        "webhook_events": service.get_webhook_events()
    }

# ------------------------------ END OF FILE ------------------------------