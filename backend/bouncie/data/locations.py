# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timezone
from typing import Optional
import logging

from ..utils import Location, MovementStatus, parse_datetime, VehicleNotFoundError, BouncieAPIError

try:
    from core.utils.logger import logger
except ImportError:
    logger = logging.getLogger(__name__)

# ------------------------------ LOCATION DATA CLASS ------------------------------

class BouncieLocationData:
    """Handles location data operations for Bouncie API."""
    
    def __init__(self, client, cache_ttl_seconds: int = 30):
        """Initialize the location data handler.
        
        Args:
            client: BouncieAPIClient instance for API requests.
            cache_ttl_seconds: Cache time-to-live in seconds (default: 30).
        """
        self.client = client
        self.cache_ttl_seconds = cache_ttl_seconds
        self._vehicles_cache: Optional[list] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def _get_vehicle(self, imei: Optional[str] = None) -> dict:
        """Get vehicle data by IMEI or first available vehicle."""
        # Caching check - essential for multiple vehicles
        if (self._vehicles_cache and self._cache_timestamp and 
            (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds() < self.cache_ttl_seconds):
            vehicles = self._vehicles_cache
        else:
            vehicles_result = await self.client.get_vehicles()
            if not vehicles_result.get("success") or not vehicles_result.get("data"):
                raise BouncieAPIError("Failed to get vehicles data")
            
            vehicles = vehicles_result["data"]
            if not isinstance(vehicles, list) or len(vehicles) == 0:
                raise BouncieAPIError("No vehicles found")
            
            self._vehicles_cache = vehicles
            self._cache_timestamp = datetime.now(timezone.utc)
        
        if imei:
            vehicle = next((v for v in vehicles if v.get("imei") == imei), None)
            if not vehicle:
                raise VehicleNotFoundError(f"Vehicle with IMEI {imei} not found")
            return vehicle
        else:
            return vehicles[0]
    
    async def get_current_location(self, imei: Optional[str] = None) -> Optional[Location]:
        """Get current GPS location of vehicle."""
        try:
            vehicle = await self._get_vehicle(imei)
            stats = vehicle.get("stats", {})
            location = stats.get("location", {})
            
            return Location(
                imei=vehicle.get("imei", ""),
                name=vehicle.get("nickName", ""),
                latitude=location.get("lat"),
                longitude=location.get("lon"),
                heading=location.get("heading"),
                address=location.get("address"),
                last_updated=parse_datetime(stats.get("lastUpdated"))
            )
        except (VehicleNotFoundError, BouncieAPIError) as e:
            logger.error(f"Error getting current location: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error getting current location: {e}")
            return None
    
    async def is_vehicle_moving(self, imei: Optional[str] = None) -> Optional[MovementStatus]:
        """Check if vehicle is currently moving."""
        try:
            vehicle = await self._get_vehicle(imei)
            stats = vehicle.get("stats", {})
            speed = stats.get("speed", 0)
            is_running = stats.get("isRunning", False)
            
            return MovementStatus(
                imei=vehicle.get("imei", ""),
                name=vehicle.get("nickName", ""),
                is_moving=speed > 0,
                is_running=is_running,
                current_speed=speed,
                status="Moving" if speed > 0 else "Stopped"
            )
        except (VehicleNotFoundError, BouncieAPIError) as e:
            logger.error(f"Error checking vehicle movement: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error checking vehicle movement: {e}")
            return None

# ------------------------------ END OF FILE ------------------------------