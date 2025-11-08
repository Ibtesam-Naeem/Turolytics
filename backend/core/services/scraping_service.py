# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
from typing import Optional, Dict, Any, Sequence
from datetime import datetime
from enum import Enum

from core.config.settings import settings
from core.utils.file_storage import save_scraped_data_to_json
from core.security.session import save_storage_state

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
    
    async def _execute_scraping_session(self, scrapers: Sequence[ScrapingType], account_id: int, task_id: str, email: str = None, password: str = None) -> Dict[str, Any]:
        """Execute a scraping session with multiple scrapers.
        
        Runs multiple scrapers under a single logged-in browser session for efficiency.
        This approach reduces login overhead and maintains session state across scrapers.
        
        Args:
            scrapers: Sequence of scraper types to execute
            account_id: Account ID for data association
            task_id: Unique task identifier for tracking
            
        Returns:
            Dict containing results from all scrapers
        """
        async with self._semaphore:
            page, context, browser = None, None, None
            results = {}
        
            try:
                login_result = await complete_turo_login(headless=False, account_id=account_id, email=email, password=password)
                if not login_result:
                    raise Exception("Login failed")
                
                page, context, browser = login_result
                self._update_task_status(task_id, TaskStatus.RUNNING, "Login successful, starting scraping...", scraper_types=[t.value for t in scrapers])
                
                for scraper_type in scrapers:
                    try:
                        self._update_task_status(task_id, TaskStatus.RUNNING, f"Scraping {scraper_type.value}...", scraper_types=[t.value for t in scrapers])
                        
                        scraper_func = self._scrapers[scraper_type]
                        # Pass the logged-in page to the scraper function
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
                    # Save scraped data to JSON file
                    json_path = save_scraped_data_to_json(account_id, results, task_id)
                    
                    # Save session state for future logins
                    if context:
                        await save_storage_state(context, account_id=account_id)
                    
                    self._update_task_status(
                        task_id, 
                        TaskStatus.COMPLETED, 
                        "Scraping completed successfully",
                        {"scraped_data": results, "json_file": json_path},
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
    
    def _generate_task_id(self, scraping_type: ScrapingType, account_id: int) -> str:
        """Generate unique task ID."""
        timestamp = int(datetime.utcnow().timestamp())
        return f"{scraping_type.value}_{account_id}_{timestamp}"
    
    # ------------------------------ PUBLIC API ------------------------------
    
    async def scrape_all(self, account_id: int, email: str = None, password: str = None) -> str:
        """Scrape all data types in a single session.
        
        Args:
            account_id: Account ID to associate scraped data with
            email: Turo email for login
            password: Turo password for login
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.ALL, account_id)
        all_types = [ScrapingType.VEHICLES, ScrapingType.TRIPS, ScrapingType.EARNINGS, ScrapingType.REVIEWS]
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=[t.value for t in all_types])
        
        task = asyncio.create_task(self._execute_scraping_session(all_types, account_id, task_id, email, password))
        
        if not hasattr(self, '_background_tasks'):
            self._background_tasks = set()
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        return task_id
    
    # ------------------------------ TASK MANAGEMENT ------------------------------
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        return self.active_tasks.get(task_id)

# ------------------------------ END OF FILE ------------------------------