# ------------------------------ IMPORTS ------------------------------
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Sequence
from datetime import datetime
from enum import Enum

from core.config.settings import settings

from turo.data.login import complete_turo_login
from turo.data.vehicles import scrape_vehicle_listings
from turo.data.trips import scrape_all_trips
from turo.data.ratings import scrape_ratings_data
from turo.data.earnings import scrape_all_earnings_data

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ FILE SAVING ------------------------------
def _ensure_data_directory(account_id: int, task_id: str) -> Path:
    """Ensure data directory exists and return the path."""
    data_dir = Path("data/scraped") / str(account_id) / task_id
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def _save_to_json(data: Any, filepath: Path) -> bool:
    """Save data to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")
        return False

def _save_scraped_data(account_id: int, task_id: str, results: Dict[str, Any]) -> Dict[str, bool]:
    """Save scraped data to JSON files.
    
    Args:
        account_id: Account ID
        task_id: Task ID
        results: Dictionary containing scraped data
        
    Returns:
        Dictionary with save status for each data type
    """
    save_status = {}
    data_dir = _ensure_data_directory(account_id, task_id)
    
    for data_type, data in results.items():
        if data is not None:
            filepath = data_dir / f"{data_type}.json"
            save_status[data_type] = _save_to_json(data, filepath)
        else:
            save_status[data_type] = False
    
    # Also save combined results
    combined_path = data_dir / "all_data.json"
    save_status["all_data"] = _save_to_json(results, combined_path)
    
    return save_status

# ------------------------------ ENUMS ------------------------------
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapingType(Enum):
    VEHICLES = "vehicles"
    TRIPS = "trips"
    REVIEWS = "reviews"
    EARNINGS = "earnings"
    ALL = "all"

# ------------------------------ SCRAPING SERVICE ------------------------------
class ScrapingService:
    """Streamlined service for handling scraping operations."""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._scrapers = {
            ScrapingType.VEHICLES: self._wrap_scraper_result(scrape_vehicle_listings, "listings"),
            ScrapingType.TRIPS: scrape_all_trips,
            ScrapingType.REVIEWS: self._wrap_scraper_result(scrape_ratings_data, "ratings"),
            ScrapingType.EARNINGS: scrape_all_earnings_data,
        }
        self._semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_tasks)
    
    def _wrap_scraper_result(self, scraper_func, key):
        """Create a wrapper function for scrapers that need consistent structure."""
        async def wrapper(page):
            result = await scraper_func(page)
            return {key: result, "scraping_success": {key: result is not None}}
        return wrapper
    
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
                login_result = await complete_turo_login(headless=True, account_id=account_id, email=email, password=password)
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
                            results[scraper_type.value] = None
                            
                    except Exception as e:
                        logger.error(f"Failed to scrape {scraper_type.value}: {e}")
                        results[scraper_type.value] = None
                
                if any(results.values()):
                    # Save data to JSON files
                    self._update_task_status(task_id, TaskStatus.RUNNING, "Saving data to JSON files...", scraper_types=[t.value for t in scrapers])
                    save_status = _save_scraped_data(account_id, task_id, results)
                    
                    self._update_task_status(
                        task_id, 
                        TaskStatus.COMPLETED, 
                        "Scraping completed successfully",
                        {"scraped_data": results, "save_status": save_status},
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
    
    async def scrape_vehicles(self, account_id: int, email: str = None, password: str = None) -> str:
        """Scrape vehicles data.
        
        Args:
            account_id: Account ID to associate scraped data with
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.VEHICLES, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["vehicles"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.VEHICLES], account_id, task_id, email, password))
        return task_id
    
    async def scrape_trips(self, account_id: int, email: str = None, password: str = None) -> str:
        """Scrape trips data.
        
        Args:
            account_id: Account ID to associate scraped data with
            email: Turo email for login
            password: Turo password for login
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.TRIPS, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["trips"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.TRIPS], account_id, task_id, email, password))
        return task_id
    
    async def scrape_reviews(self, account_id: int, email: str = None, password: str = None) -> str:
        """Scrape reviews data.
        
        Args:
            account_id: Account ID to associate scraped data with
            email: Turo email for login
            password: Turo password for login
            
        Returns:
            Task ID for tracking the scraping operation
        """
        task_id = self._generate_task_id(ScrapingType.REVIEWS, account_id)
        self._update_task_status(task_id, TaskStatus.PENDING, "Queued for execution", scraper_types=["reviews"])
        asyncio.create_task(self._execute_scraping_session([ScrapingType.REVIEWS], account_id, task_id, email, password))
        return task_id
    
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
        all_types = [ScrapingType.VEHICLES, ScrapingType.TRIPS, ScrapingType.REVIEWS, ScrapingType.EARNINGS]
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