#!/usr/bin/env python3
"""
Bouncie Vehicle Data Module
Handles vehicle information, real-time status, and health monitoring
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

class BouncieVehicleData:
    """Handles vehicle data operations for Bouncie API."""
    
    def __init__(self, client):
        self.client = client
    
    async def get_vehicles(self) -> Dict[str, Any]:
        """Get all vehicles data."""
        return await self.client.get_vehicles()
    
    async def get_vehicle_by_imei(self, imei: str) -> Dict[str, Any]:
        """Get specific vehicle by IMEI."""
        vehicles_result = await self.client.get_vehicles()
        if not vehicles_result["success"]:
            return {"success": False, "error": "Failed to get vehicles data"}
        
        vehicles = vehicles_result["data"]
        if not isinstance(vehicles, list):
            return {"success": False, "error": "Invalid vehicles data"}
        
        target_vehicle = next((v for v in vehicles if v.get("imei") == imei), None)
        if not target_vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        return {"success": True, "data": target_vehicle}
    
    async def get_vehicle_status(self, imei: str = None) -> Dict[str, Any]:
        """Get real-time vehicle status."""
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
                "vehicle_info": {
                    "make": target_vehicle.get("model", {}).get("make"),
                    "model": target_vehicle.get("model", {}).get("name"),
                    "year": target_vehicle.get("model", {}).get("year"),
                    "vin": target_vehicle.get("vin")
                },
                "status": {
                    "is_running": stats.get("isRunning", False),
                    "speed": stats.get("speed", 0),
                    "fuel_level": round(stats.get("fuelLevel", 0), 2),
                    "odometer": round(stats.get("odometer", 0), 2),
                    "last_updated": stats.get("lastUpdated")
                },
                "location": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lon"),
                    "heading": location.get("heading"),
                    "address": location.get("address")
                }
            }
        }
    
    async def get_vehicle_health(self, imei: str = None) -> Dict[str, Any]:
        """Get vehicle health information."""
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
        mil = stats.get("mil", {})
        battery = stats.get("battery", {})
        
        # Calculate health score
        health_score = self._calculate_health_score(mil, battery)
        
        return {
            "success": True,
            "data": {
                "vehicle_imei": target_vehicle.get("imei"),
                "vehicle_name": target_vehicle.get("nickName"),
                "health": {
                    "overall_score": health_score,
                    "status": self._get_health_status(health_score),
                    "battery": {
                        "status": battery.get("status", "unknown"),
                        "is_healthy": battery.get("status") == "normal",
                        "last_updated": battery.get("lastUpdated")
                    },
                    "check_engine": {
                        "mil_on": mil.get("milOn", False),
                        "dtc_codes": mil.get("qualifiedDtcList", []),
                        "needs_attention": mil.get("milOn", False) or len(mil.get("qualifiedDtcList", [])) > 0
                    }
                }
            }
        }
    
    def _calculate_health_score(self, mil: Dict, battery: Dict) -> int:
        """Calculate overall vehicle health score (0-100)."""
        score = 100
        
        # Deduct points for check engine issues
        if mil.get("milOn", False):
            score -= 30
        
        # Deduct points for DTC codes
        dtc_count = len(mil.get("qualifiedDtcList", []))
        score -= dtc_count * 10
        
        # Deduct points for battery issues
        battery_status = battery.get("status", "normal")
        if battery_status == "critical":
            score -= 25
        elif battery_status == "low":
            score -= 15
        elif battery_status != "normal":
            score -= 10
        
        return max(0, min(100, score))
    
    def _get_health_status(self, score: int) -> str:
        """Get health status based on score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"
