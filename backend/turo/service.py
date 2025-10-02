# ------------------------------ IMPORTS ------------------------------
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from core.utils.browser import launch_browser
from core.security.session import get_storage_state, save_storage_state, verify_session_authenticated
from .login import complete_turo_login
from .vehicles import scrape_all_vehicle_data
from .trips import scrape_all_trips
from .earnings import scrape_all_earnings_data
from .ratings import scrape_all_ratings_data
from core.db.operations.turo import save_scraped_data

logger = logging.getLogger(__name__)

# ------------------------------ SCRAPING SERVICE ------------------------------

class ScrapingService:
    """Service for managing Turo data scraping operations."""
    
    def __init__(self):
        self.tasks = {}
        self.task_count = {
            'vehicles': 0,
            'trips': 0,
            'earnings': 0,
            'reviews': 0,
            'all': 0
        }
    
    async def scrape_vehicles(self, account_id: int) -> str:
        """Scrape vehicle data for an account."""
        task_id = f"vehicles_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks[task_id] = {
            'status': 'running',
            'type': 'vehicles',
            'account_id': account_id,
            'started_at': datetime.now().isoformat()
        }
        self.task_count['vehicles'] += 1
        
        try:
            # Run scraping in background
            asyncio.create_task(self._scrape_vehicles_task(task_id, account_id))
            return task_id
        except Exception as e:
            logger.error(f"Error starting vehicle scraping: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            return task_id
    
    async def scrape_trips(self, account_id: int) -> str:
        """Scrape trip data for an account."""
        task_id = f"trips_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks[task_id] = {
            'status': 'running',
            'type': 'trips',
            'account_id': account_id,
            'started_at': datetime.now().isoformat()
        }
        self.task_count['trips'] += 1
        
        try:
            asyncio.create_task(self._scrape_trips_task(task_id, account_id))
            return task_id
        except Exception as e:
            logger.error(f"Error starting trip scraping: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            return task_id
    
    async def scrape_earnings(self, account_id: int) -> str:
        """Scrape earnings data for an account."""
        task_id = f"earnings_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks[task_id] = {
            'status': 'running',
            'type': 'earnings',
            'account_id': account_id,
            'started_at': datetime.now().isoformat()
        }
        self.task_count['earnings'] += 1
        
        try:
            asyncio.create_task(self._scrape_earnings_task(task_id, account_id))
            return task_id
        except Exception as e:
            logger.error(f"Error starting earnings scraping: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            return task_id
    
    async def scrape_reviews(self, account_id: int) -> str:
        """Scrape review data for an account."""
        task_id = f"reviews_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks[task_id] = {
            'status': 'running',
            'type': 'reviews',
            'account_id': account_id,
            'started_at': datetime.now().isoformat()
        }
        self.task_count['reviews'] += 1
        
        try:
            asyncio.create_task(self._scrape_reviews_task(task_id, account_id))
            return task_id
        except Exception as e:
            logger.error(f"Error starting review scraping: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            return task_id
    
    async def scrape_all(self, account_id: int) -> str:
        """Scrape all data for an account."""
        task_id = f"all_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks[task_id] = {
            'status': 'running',
            'type': 'all',
            'account_id': account_id,
            'started_at': datetime.now().isoformat()
        }
        self.task_count['all'] += 1
        
        try:
            asyncio.create_task(self._scrape_all_task(task_id, account_id))
            return task_id
        except Exception as e:
            logger.error(f"Error starting all scraping: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            return task_id
    
    # ------------------------------ TASK IMPLEMENTATIONS ------------------------------
    
    async def _scrape_vehicles_task(self, task_id: str, account_id: int):
        """Background task for scraping vehicles."""
        try:
            page, context, browser = await launch_browser(headless=True)
            
            # Check for existing session
            storage_state = get_storage_state(account_id)
            if storage_state:
                context = await browser.new_context(storage_state=storage_state)
                page = await context.new_page()
            
            # Verify session or login
            if not await verify_session_authenticated(page):
                page, context, browser = await complete_turo_login(headless=True, account_id=account_id)
            
            # Scrape vehicles
            vehicles_data = await scrape_all_vehicle_data(page)
            
            # Save data
            if vehicles_data:
                save_scraped_data(account_id, {'vehicles': vehicles_data})
            
            # Save session
            await save_storage_state(context, account_id)
            
            # Update task status
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['data_count'] = len(vehicles_data.get('vehicles', []))
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in vehicle scraping task {task_id}: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
    
    async def _scrape_trips_task(self, task_id: str, account_id: int):
        """Background task for scraping trips."""
        try:
            page, context, browser = await launch_browser(headless=True)
            
            storage_state = get_storage_state(account_id)
            if storage_state:
                context = await browser.new_context(storage_state=storage_state)
                page = await context.new_page()
            
            if not await verify_session_authenticated(page):
                page, context, browser = await complete_turo_login(headless=True, account_id=account_id)
            
            trips_data = await scrape_all_trips(page)
            
            if trips_data:
                save_scraped_data(account_id, {'trips': trips_data})
            
            await save_storage_state(context, account_id)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['data_count'] = len(trips_data.get('trips', []))
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in trip scraping task {task_id}: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
    
    async def _scrape_earnings_task(self, task_id: str, account_id: int):
        """Background task for scraping earnings."""
        try:
            page, context, browser = await launch_browser(headless=True)
            
            storage_state = get_storage_state(account_id)
            if storage_state:
                context = await browser.new_context(storage_state=storage_state)
                page = await context.new_page()
            
            if not await verify_session_authenticated(page):
                page, context, browser = await complete_turo_login(headless=True, account_id=account_id)
            
            earnings_data = await scrape_all_earnings_data(page)
            
            if earnings_data:
                save_scraped_data(account_id, {'earnings': earnings_data})
            
            await save_storage_state(context, account_id)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['data_count'] = len(earnings_data.get('breakdown', []))
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in earnings scraping task {task_id}: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
    
    async def _scrape_reviews_task(self, task_id: str, account_id: int):
        """Background task for scraping reviews."""
        try:
            page, context, browser = await launch_browser(headless=True)
            
            storage_state = get_storage_state(account_id)
            if storage_state:
                context = await browser.new_context(storage_state=storage_state)
                page = await context.new_page()
            
            if not await verify_session_authenticated(page):
                page, context, browser = await complete_turo_login(headless=True, account_id=account_id)
            
            reviews_data = await scrape_all_ratings_data(page)
            
            if reviews_data:
                save_scraped_data(account_id, {'reviews': reviews_data})
            
            await save_storage_state(context, account_id)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['data_count'] = len(reviews_data.get('reviews', []))
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in review scraping task {task_id}: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
    
    async def _scrape_all_task(self, task_id: str, account_id: int):
        """Background task for scraping all data."""
        try:
            page, context, browser = await launch_browser(headless=True)
            
            storage_state = get_storage_state(account_id)
            if storage_state:
                context = await browser.new_context(storage_state=storage_state)
                page = await context.new_page()
            
            if not await verify_session_authenticated(page):
                page, context, browser = await complete_turo_login(headless=True, account_id=account_id)
            
            # Scrape all data types
            all_data = {}
            
            vehicles_data = await scrape_all_vehicle_data(page)
            if vehicles_data:
                all_data['vehicles'] = vehicles_data
            
            trips_data = await scrape_all_trips(page)
            if trips_data:
                all_data['trips'] = trips_data
            
            earnings_data = await scrape_all_earnings_data(page)
            if earnings_data:
                all_data['earnings'] = earnings_data
            
            reviews_data = await scrape_all_ratings_data(page)
            if reviews_data:
                all_data['reviews'] = reviews_data
            
            # Save all data
            if all_data:
                save_scraped_data(account_id, all_data)
            
            await save_storage_state(context, account_id)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['data_count'] = sum(len(data) for data in all_data.values())
            
            await browser.close()
            
        except Exception as e:
            logger.error(f"Error in all scraping task {task_id}: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
    
    # ------------------------------ TASK MANAGEMENT ------------------------------
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks."""
        return self.tasks
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        return self.tasks.get(task_id)
    
    def get_task_count(self) -> Dict[str, int]:
        """Get task counts by type."""
        return self.task_count.copy()
    
    def clear_completed_tasks(self):
        """Clear completed and failed tasks."""
        self.tasks = {k: v for k, v in self.tasks.items() 
                     if v.get('status') not in ['completed', 'failed']}

# ------------------------------ END OF FILE ------------------------------
