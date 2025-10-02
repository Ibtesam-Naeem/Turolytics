# ------------------------------ IMPORTS ------------------------------
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from core.utils.logger import logger
from .auth import auth_manager, get_bouncie_auth_headers

# ------------------------------ BOUNCIE SERVICE CLASS ------------------------------

class BouncieService:
    """Main Bouncie service for API interactions."""
    
    def __init__(self):
        self.api_base_url = "https://api.bouncie.dev/v1"
        logger.info("BouncieService initialized")
    
    async def _make_api_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an authenticated API request to Bouncie."""
        try:
            headers = await get_bouncie_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}{endpoint}"
                
                async with session.request(
                    method, url, headers=headers, params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "data": data,
                            "status_code": response.status
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "status_code": response.status
                        }
                        
        except Exception as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information."""
        try:
            logger.info("Fetching user information...")
            result = await self._make_api_request("GET", "/user")
            
            if result["success"]:
                logger.info("Successfully fetched user information")
                return result
            else:
                logger.error(f"Failed to fetch user information: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching user information: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_vehicles(self) -> Dict[str, Any]:
        """Get vehicles information."""
        try:
            logger.info("Fetching vehicles information...")
            result = await self._make_api_request("GET", "/vehicles")
            
            if result["success"]:
                vehicles = result["data"]
                if isinstance(vehicles, list):
                    logger.info(f"Successfully fetched {len(vehicles)} vehicles")
                else:
                    logger.info("Successfully fetched vehicles data")
                return result
            else:
                logger.error(f"Failed to fetch vehicles: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching vehicles: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_locations(self) -> Dict[str, Any]:
        """Get locations information."""
        try:
            logger.info("Fetching locations information...")
            result = await self._make_api_request("GET", "/locations")
            
            if result["success"]:
                locations = result["data"]
                if isinstance(locations, list):
                    logger.info(f"Successfully fetched {len(locations)} locations")
                else:
                    logger.info("Successfully fetched locations data")
                return result
            else:
                logger.error(f"Failed to fetch locations: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching locations: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_trips(self, gps_format: str = "geojson", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get trips information with required parameters."""
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            params = {
                "gpsFormat": gps_format,
                "startDate": start_date,
                "endDate": end_date
            }
            
            logger.info(f"Fetching trips from {start_date} to {end_date}...")
            result = await self._make_api_request("GET", "/trips", params)
            
            if result["success"]:
                trips = result["data"]
                if isinstance(trips, list):
                    logger.info(f"Successfully fetched {len(trips)} trips")
                else:
                    logger.info("Successfully fetched trips data")
                return result
            else:
                logger.error(f"Failed to fetch trips: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching trips: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_vehicle_trips(self, vehicle_id: str, gps_format: str = "geojson", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get trips for a specific vehicle."""
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            params = {
                "gpsFormat": gps_format,
                "startDate": start_date,
                "endDate": end_date
            }
            
            logger.info(f"Fetching trips for vehicle {vehicle_id}...")
            result = await self._make_api_request("GET", f"/vehicles/{vehicle_id}/trips", params)
            
            if result["success"]:
                trips = result["data"]
                if isinstance(trips, list):
                    logger.info(f"Successfully fetched {len(trips)} trips for vehicle {vehicle_id}")
                else:
                    logger.info(f"Successfully fetched trips data for vehicle {vehicle_id}")
                return result
            else:
                logger.error(f"Failed to fetch trips for vehicle {vehicle_id}: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching trips for vehicle {vehicle_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_vehicle_location(self, vehicle_id: str) -> Dict[str, Any]:
        """Get current location of a specific vehicle."""
        try:
            logger.info(f"Fetching location for vehicle {vehicle_id}...")
            result = await self._make_api_request("GET", f"/vehicles/{vehicle_id}/location")
            
            if result["success"]:
                logger.info(f"Successfully fetched location for vehicle {vehicle_id}")
                return result
            else:
                logger.error(f"Failed to fetch location for vehicle {vehicle_id}: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching location for vehicle {vehicle_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def get_vehicle_diagnostics(self, vehicle_id: str) -> Dict[str, Any]:
        """Get diagnostics for a specific vehicle."""
        try:
            logger.info(f"Fetching diagnostics for vehicle {vehicle_id}...")
            result = await self._make_api_request("GET", f"/vehicles/{vehicle_id}/diagnostics")
            
            if result["success"]:
                logger.info(f"Successfully fetched diagnostics for vehicle {vehicle_id}")
                return result
            else:
                logger.error(f"Failed to fetch diagnostics for vehicle {vehicle_id}: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error fetching diagnostics for vehicle {vehicle_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """Sync all available Bouncie data."""
        try:
            logger.info("Starting full Bouncie data sync...")
            
            results = {}
            
            # Get user info
            user_result = await self.get_user_info()
            results["user"] = user_result
            
            # Get vehicles
            vehicles_result = await self.get_vehicles()
            results["vehicles"] = vehicles_result
            
            # Get locations
            locations_result = await self.get_locations()
            results["locations"] = locations_result
            
            # Get trips
            trips_result = await self.get_trips()
            results["trips"] = trips_result
            
            # Count successful operations
            successful = sum(1 for result in results.values() if result.get("success", False))
            total = len(results)
            
            logger.info(f"Data sync completed: {successful}/{total} operations successful")
            
            return {
                "success": successful > 0,
                "results": results,
                "successful_count": successful,
                "total_count": total
            }
            
        except Exception as e:
            logger.error(f"Error during data sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {}
            }

# ------------------------------ GLOBAL SERVICE INSTANCE ------------------------------

bouncie_service = BouncieService()

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def get_user_info() -> Dict[str, Any]:
    """Get user information."""
    return await bouncie_service.get_user_info()

async def get_vehicles() -> Dict[str, Any]:
    """Get vehicles information."""
    return await bouncie_service.get_vehicles()

async def get_locations() -> Dict[str, Any]:
    """Get locations information."""
    return await bouncie_service.get_locations()

async def get_trips(gps_format: str = "geojson", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Get trips information."""
    return await bouncie_service.get_trips(gps_format, start_date, end_date)

async def sync_all_data() -> Dict[str, Any]:
    """Sync all available Bouncie data."""
    return await bouncie_service.sync_all_data()

# ------------------------------ END OF FILE ------------------------------
