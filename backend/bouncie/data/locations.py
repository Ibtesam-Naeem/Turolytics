#!/usr/bin/env python3
"""
Bouncie Location Data Module
Handles location tracking and GPS data
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

class BouncieLocationData:
    """Handles location data operations for Bouncie API."""
    
    def __init__(self, client):
        self.client = client
    
    async def get_current_location(self, imei: str = None) -> Dict[str, Any]:
        """Get current GPS location of vehicle."""
        vehicles_result = await self.client.get_vehicles()
        if not vehicles_result["success"]:
            return {"success": False, "error": "Failed to get vehicles data"}
        
        vehicles = vehicles_result["data"]
        if not isinstance(vehicles, list) or len(vehicles) == 0:
            return {"success": False, "error": "No vehicles found"}
        
        target_vehicle = None
        if imei:
            target_vehicle = next((v for v in vehicles if v.get("imei") == imei), None)
        else:
            target_vehicle = vehicles[0]
        
        if not target_vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        stats = target_vehicle.get("stats", {})
        location = stats.get("location", {})
        
        return {
            "success": True,
            "data": {
                "vehicle_imei": target_vehicle.get("imei"),
                "vehicle_name": target_vehicle.get("nickName"),
                "location": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lon"),
                    "heading": location.get("heading"),
                    "address": location.get("address")
                },
                "last_updated": stats.get("lastUpdated")
            }
        }
    
    async def get_location_history(self, imei: str = None, days: int = 7) -> Dict[str, Any]:
        """Get location history for a vehicle."""
        # This would typically query a database for historical location data
        # For now, return current location as a placeholder
        current_location = await self.get_current_location(imei)
        if not current_location["success"]:
            return current_location
        
        # In a real implementation, you would:
        # 1. Query your database for historical location data
        # 2. Filter by date range
        # 3. Return formatted location history
        
        return {
            "success": True,
            "data": {
                "vehicle_imei": current_location["data"]["vehicle_imei"],
                "vehicle_name": current_location["data"]["vehicle_name"],
                "history_period": f"{days} days",
                "locations": [current_location["data"]["location"]],  # Placeholder
                "total_points": 1,
                "message": "Location history would be retrieved from database"
            }
        }
    
    async def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula."""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        return c * r
    
    async def is_vehicle_moving(self, imei: str = None) -> Dict[str, Any]:
        """Check if vehicle is currently moving."""
        vehicles_result = await self.client.get_vehicles()
        if not vehicles_result["success"]:
            return {"success": False, "error": "Failed to get vehicles data"}
        
        vehicles = vehicles_result["data"]
        if not isinstance(vehicles, list) or len(vehicles) == 0:
            return {"success": False, "error": "No vehicles found"}
        
        target_vehicle = None
        if imei:
            target_vehicle = next((v for v in vehicles if v.get("imei") == imei), None)
        else:
            target_vehicle = vehicles[0]
        
        if not target_vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        stats = target_vehicle.get("stats", {})
        speed = stats.get("speed", 0)
        is_running = stats.get("isRunning", False)
        
        return {
            "success": True,
            "data": {
                "vehicle_imei": target_vehicle.get("imei"),
                "vehicle_name": target_vehicle.get("nickName"),
                "movement": {
                    "is_moving": speed > 0,
                    "is_running": is_running,
                    "current_speed": speed,
                    "status": "Moving" if speed > 0 else "Stopped"
                }
            }
        }
