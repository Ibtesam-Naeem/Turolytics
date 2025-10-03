#!/usr/bin/env python3
"""
Bouncie Trip Data Module
Handles trip data and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class BouncieTripData:
    """Handles trip data operations for Bouncie API."""
    
    def __init__(self, client):
        self.client = client
    
    async def get_trips(self, gps_format: str = "latlng", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get trips data with date parameters."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        return await self.client.get_trips(gps_format, start_date, end_date)
    
    async def get_recent_trips(self, days: int = 7) -> Dict[str, Any]:
        """Get recent trips for the last N days."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_trips(start_date=start_date, end_date=end_date)
    
    async def get_trip_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get trip analytics for a period."""
        trips_result = await self.get_recent_trips(days)
        if not trips_result["success"]:
            return trips_result
        
        trips = trips_result["data"]
        if not isinstance(trips, list):
            return {"success": False, "error": "Invalid trips data format"}
        
        # Calculate analytics
        total_trips = len(trips)
        total_distance = sum(trip.get("distance", 0) for trip in trips)
        total_duration = sum(trip.get("duration", 0) for trip in trips)
        
        analytics = {
            "period_days": days,
            "total_trips": total_trips,
            "total_distance": round(total_distance, 2),
            "total_duration": round(total_duration, 2),
            "average_distance": round(total_distance / max(total_trips, 1), 2),
            "average_duration": round(total_duration / max(total_trips, 1), 2),
            "trips_per_day": round(total_trips / days, 2)
        }
        
        return {
            "success": True,
            "data": analytics
        }
    
    async def get_trip_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get trip summary for dashboard display."""
        trips_result = await self.get_recent_trips(days)
        if not trips_result["success"]:
            return trips_result
        
        trips = trips_result["data"]
        if not isinstance(trips, list):
            return {"success": False, "error": "Invalid trips data format"}
        
        # Get recent trips (last 5)
        recent_trips = trips[:5] if len(trips) > 5 else trips
        
        summary = {
            "period_days": days,
            "total_trips": len(trips),
            "recent_trips": recent_trips,
            "last_trip": trips[0] if trips else None,
            "message": "Trip data retrieved successfully"
        }
        
        return {
            "success": True,
            "data": summary
        }
