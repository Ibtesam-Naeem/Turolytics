# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
from typing import Optional, Dict, Any, Sequence
from datetime import datetime
from enum import Enum

from core.config.settings import settings
from core.security.session import save_storage_state
from core.database import SessionLocal
from core.database.db_service import DatabaseService

from turo.data.login import complete_turo_login
from turo.data.vehicles import scrape_vehicle_listings
from turo.data.trips import scrape_all_trips
from turo.data.earnings import scrape_earnings_data
from turo.data.ratings import scrape_ratings_data


# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ ENUMS ------------------------------
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapingType(Enum):
    VEHICLES = "vehicles"
    TRIPS = "trips"
    EARNINGS = "earnings"
    REVIEWS = "reviews"
    ALL = "all"

# ------------------------------ SCRAPING SERVICE ------------------------------
class ScrapingService:
    """Streamlined service for handling scraping operations."""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._scrapers = {
            ScrapingType.VEHICLES: scrape_vehicle_listings,
            ScrapingType.TRIPS: scrape_all_trips,
            ScrapingType.EARNINGS: scrape_earnings_data,
            ScrapingType.REVIEWS: scrape_ratings_data,
        }
        self._semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_tasks)
        self._background_tasks: set = set()
        self._all_scraper_types = list(self._scrapers.keys())
    
    async def _execute_scraping_session(self, scrapers: Sequence[ScrapingType], user_id: int, task_id: str, email: str = None, password: str = None) -> Dict[str, Any]:
        """Execute a scraping session with multiple scrapers."""
        async with self._semaphore:
            page, context, browser = None, None, None
            results = {}
        
            try:
                db = SessionLocal()
                try:
                    existing_trip_ids = DatabaseService.get_existing_trip_ids(db, user_id)
                    existing_customer_ids = DatabaseService.get_existing_customer_ids(db, user_id)
                    logger.info(f"Found {len(existing_trip_ids)} existing trips and {len(existing_customer_ids)} existing reviews - will skip these during scraping")
                except Exception as e:
                    logger.warning(f"Error fetching existing IDs: {e}. Will scrape all data.")
                    existing_trip_ids = set()
                    existing_customer_ids = set()
                finally:
                    db.close()
                
                login_result = await complete_turo_login(account_id=user_id, email=email, password=password)
                if not login_result:
                    raise RuntimeError("Login failed - unable to authenticate with Turo")
                
                page, context, browser = login_result
                self._update_task_status(task_id, TaskStatus.RUNNING, "Login successful, starting scraping...", scraper_types=[t.value for t in scrapers])
                
                for scraper_type in scrapers:
                    try:
                        logger.info(f"Scraping {scraper_type.value}...")
                        scraper_func = self._scrapers[scraper_type]
                        
                        if scraper_type == ScrapingType.TRIPS:
                            data = await scraper_func(page, existing_trip_ids=existing_trip_ids)
                        elif scraper_type == ScrapingType.REVIEWS:
                            data = await scraper_func(page, existing_customer_ids=existing_customer_ids)
                        else:
                            data = await scraper_func(page)
                        
                        if data:
                            results[scraper_type.value] = data
                            logger.info(f"Successfully scraped {scraper_type.value}")
                        else:
                            logger.warning(f"No data returned for {scraper_type.value} - scraper completed but found no data")
                            
                    except Exception as e:
                        logger.error(f"Failed to scrape {scraper_type.value}: {e}")
                        results[scraper_type.value] = None
                
                if any(results.values()):
                    if context:
                        await save_storage_state(context, account_id=user_id)
                    
                    db = SessionLocal()
                    try:
                        DatabaseService.save_scraped_data(db, user_id, email, results)
                        logger.info(f"Successfully saved scraped data to database for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error saving scraped data to database: {e}")
                    finally:
                        db.close()
                    
                    self._update_task_status(
                        task_id, 
                        TaskStatus.COMPLETED, 
                        "Scraping completed successfully",
                        {"scraped_data": results},
                        scraper_types=[t.value for t in scrapers]
                    )
                else:
                    self._update_task_status(task_id, TaskStatus.FAILED, "No data scraped from any source", scraper_types=[t.value for t in scrapers])
                    
            except Exception as e:
                logger.error(f"Scraping session failed: {e}")
                self._update_task_status(task_id, TaskStatus.FAILED, f"Session failed: {str(e)}", scraper_types=[t.value for t in scrapers])
            finally:
                if browser:
                    try:
                        await browser.close()
                        logger.info("Browser closed successfully")

                    except Exception as e:
                        logger.warning(f"Error closing browser: {e}")
    
    def _update_task_status(self, task_id: str, status: TaskStatus, message: str = "", data: Dict = None, started_at: str = None, scraper_types: list = None):
        """Update task status with enhanced tracking."""
        current_time = datetime.utcnow().isoformat()
        
        if task_id not in self.active_tasks:
            self.active_tasks[task_id] = {
                "started_at": started_at or current_time,
                "finished_at": None,
                "scraper_types": scraper_types or []
            }
        
        update_data = {
            "status": status.value,
            "message": message,
            "data": data or {},
            "updated_at": current_time
        }
        
        if scraper_types is not None:
            update_data["scraper_types"] = scraper_types
        
        self.active_tasks[task_id].update(update_data)
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.active_tasks[task_id]["finished_at"] = current_time
    
    def _generate_task_id(self, scraping_type: ScrapingType, user_id: int) -> str:
        """Generate unique task ID."""
        timestamp = int(datetime.utcnow().timestamp())
        return f"{scraping_type.value}_{user_id}_{timestamp}"
    
    # ------------------------------ PUBLIC API ------------------------------
    
    async def _scrape(self, scraping_type: ScrapingType, user_id: int, email: str = None, password: str = None) -> str:
        """Internal method to scrape data of specified type."""
        if scraping_type == ScrapingType.ALL:
            scrapers = self._all_scraper_types
        else:
            scrapers = [scraping_type]
        
        task_id = self._generate_task_id(scraping_type, user_id)
        self._update_task_status(
            task_id, 
            TaskStatus.PENDING, 
            "Queued for execution", 
            scraper_types=[s.value for s in scrapers]
        )
        
        task = asyncio.create_task(self._execute_scraping_session(scrapers, user_id, task_id, email, password))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        return task_id
    
    async def scrape_all(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape all data types in a single session."""
        return await self._scrape(ScrapingType.ALL, user_id, email, password)
    
    async def scrape_vehicles(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape vehicles only."""
        return await self._scrape(ScrapingType.VEHICLES, user_id, email, password)
    
    async def scrape_trips(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape trips only."""
        return await self._scrape(ScrapingType.TRIPS, user_id, email, password)
    
    async def scrape_reviews(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape reviews only."""
        return await self._scrape(ScrapingType.REVIEWS, user_id, email, password)
    
    async def scrape_earnings(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape earnings only."""
        return await self._scrape(ScrapingType.EARNINGS, user_id, email, password)
    
    # ------------------------------ TASK MANAGEMENT ------------------------------
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        return self.active_tasks.get(task_id)

# ------------------------------ END OF FILE ------------------------------