# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Sequence
from datetime import datetime
from enum import Enum

from core.config.settings import settings

from turo.data.login import complete_turo_login
from turo.data.vehicles import scrape_all_vehicle_data
from turo.data.trips import scrape_all_trips
from turo.data.earnings import scrape_all_earnings_data
from turo.data.ratings import scrape_all_ratings_data

from core.db.operations.turo_operations import save_scraped_data

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
            ScrapingType.VEHICLES: scrape_all_vehicle_data,
            ScrapingType.TRIPS: scrape_all_trips,
            ScrapingType.EARNINGS: scrape_all_earnings_data,
            ScrapingType.REVIEWS: scrape_all_ratings_data,
        }
        self._semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_tasks)
    
    async def _execute_scraping_session(self, scrapers: Sequence[ScrapingType], account_id: int, task_id: str) -> Dict[str, Any]:
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
                login_result = await complete_turo_login(headless=False)
                if not login_result:
                    raise Exception("Login failed")
                
                page, context, browser = login_result
                self._update_task_status(task_id, TaskStatus.RUNNING, "Login successful, starting scraping...", scraper_types=[t.value for t in scrapers])
                
                for scraper_type in scrapers:
                    try:
                        self._update_task_status(task_id, TaskStatus.RUNNING, f"Scraping {scraper_type.value}...", scraper_types=[t.value for t in scrapers])
                        
                        scraper_func = self._scrapers[scraper_type]
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
                    self._update_task_status(task_id, TaskStatus.RUNNING, "Saving data to database...", scraper_types=[t.value for t in scrapers])
                    save_results = save_scraped_data(account_id, results)
                    
                    self._update_task_status(
                        task_id, 
                        TaskStatus.COMPLETED, 
                        f"Scraping completed. Saved: {save_results}",
                        {"save_results": save_results, "scraped_data": results},
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
    
    async def scrape_vehicles(self, account_id: int) -> str:
        """Scrape vehicles data.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.VEHICLES, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["vehicles"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.VEHICLES], account_id, task_id))
        return task_id
    
    async def scrape_trips(self, account_id: int) -> str:
        """Scrape trips data.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.TRIPS, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["trips"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.TRIPS], account_id, task_id))
        return task_id
    
    async def scrape_earnings(self, account_id: int) -> str:
        """Scrape earnings data.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.EARNINGS, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["earnings"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.EARNINGS], account_id, task_id))
        return task_id
    
    async def scrape_reviews(self, account_id: int) -> str:
        """Scrape reviews data.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.REVIEWS, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["reviews"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.REVIEWS], account_id, task_id))
        return task_id
    
    async def scrape_all(self, account_id: int) -> str:
        """Scrape all data types in a single session.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.ALL, account_id)
        all_types = [ScrapingType.VEHICLES, ScrapingType.TRIPS, ScrapingType.EARNINGS, ScrapingType.REVIEWS]
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=[t.value for t in all_types])
        
        task = asyncio.create_task(self._execute_scraping_session(all_types, account_id, task_id))
        
        if not hasattr(self, '_background_tasks'):
            self._background_tasks = set()
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        return task_id
    
    # ------------------------------ TASK MANAGEMENT ------------------------------
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        return self.active_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all tasks."""
        return self.active_tasks
    
    def clear_completed_tasks(self, keep_recent: int = 10):
        """Clear completed and failed tasks, keeping recent ones for debugging.
        
        Args:
            keep_recent: Number of recent completed/failed tasks to retain
        """
        completed_tasks = [
            (task_id, task_data) 
            for task_id, task_data in self.active_tasks.items() 
            if task_data["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]
        ]
        
        completed_tasks.sort(key=lambda x: x[1]["updated_at"], reverse=True)
        recent_completed = {task_id: task_data for task_id, task_data in completed_tasks[:keep_recent]}
        
        self.active_tasks = {
            task_id: task_data 
            for task_id, task_data in self.active_tasks.items() 
            if task_data["status"] == TaskStatus.RUNNING.value
        }
        
        self.active_tasks.update(recent_completed)
        
        logger.info(f"Cleared old tasks, kept {len(recent_completed)} recent completed/failed tasks")
    
    def get_task_count(self) -> Dict[str, int]:
        """Get task count by status."""
        counts = {status.value: 0 for status in TaskStatus}
        for task_data in self.active_tasks.values():
            counts[task_data["status"]] += 1
        return counts

# ------------------------------ END OF FILE ------------------------------