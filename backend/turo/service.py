# ------------------------------ IMPORTS ------------------------------
from typing import Dict, Any, Optional
import logging

from core.services.scraping_service import ScrapingService
from core.db.operations.turo_operations import create_account, get_database_stats, get_or_create_account

logger = logging.getLogger(__name__)

# ------------------------------ TURO SERVICE ------------------------------

class TuroService:
    """Service layer for Turo-related operations."""
    
    def __init__(self):
        self.scraping_service = ScrapingService()
    
    async def scrape_account_data(self, email: str, data_types: list[str] = None) -> Dict[str, Any]:
        """Scrape data for a Turo account.
        
        Args:
            email: Turo account email.
            data_types: List of data types to scrape. If None, scrapes all.
            
        Returns:
            Dictionary containing scraping results and task IDs.
        """
        try:
            account = get_or_create_account(email)
            account_id = account.id
            
            if not data_types:
                data_types = ["vehicles", "trips", "earnings", "reviews"]
            
            results = {}
            
            if "vehicles" in data_types:
                task_id = await self.scraping_service.scrape_vehicles(account_id)
                results["vehicles_task_id"] = task_id
            
            if "trips" in data_types:
                task_id = await self.scraping_service.scrape_trips(account_id)
                results["trips_task_id"] = task_id
            
            if "earnings" in data_types:
                task_id = await self.scraping_service.scrape_earnings(account_id)
                results["earnings_task_id"] = task_id
            
            if "reviews" in data_types:
                task_id = await self.scraping_service.scrape_reviews(account_id)
                results["reviews_task_id"] = task_id
            
            if len(data_types) == 4:
                task_id = await self.scraping_service.scrape_all(account_id)
                results["all_data_task_id"] = task_id
            
            results["account_id"] = account_id
            results["email"] = email
            results["requested_types"] = data_types
            
            logger.info(f"Started scraping tasks for account {account_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error starting scraping for account {email}: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a scraping task.
        
        Args:
            task_id: Task ID to check.
            
        Returns:
            Task status dictionary or None if not found.
        """
        return self.scraping_service.get_task_status(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active scraping tasks.
        
        Returns:
            Dictionary of all tasks.
        """
        return self.scraping_service.get_all_tasks()
    
    def get_account_stats(self, account_id: int) -> Dict[str, Any]:
        """Get database statistics for an account.
        
        Args:
            account_id: Account ID to get stats for.
            
        Returns:
            Dictionary with account statistics.
        """
        try:
            stats = get_database_stats(account_id)
            return {
                "account_id": account_id,
                "database_stats": stats,
                "scraping_tasks": self.scraping_service.get_task_count()
            }
        except Exception as e:
            logger.error(f"Error getting stats for account {account_id}: {e}")
            raise
    
    def clear_completed_tasks(self, keep_recent: int = 10) -> Dict[str, Any]:
        """Clear completed and failed tasks.
        
        Args:
            keep_recent: Number of recent tasks to keep.
            
        Returns:
            Dictionary with cleanup results.
        """
        try:
            self.scraping_service.clear_completed_tasks(keep_recent)
            return {
                "message": f"Cleared completed tasks, kept {keep_recent} recent ones",
                "remaining_tasks": len(self.scraping_service.get_all_tasks())
            }
        except Exception as e:
            logger.error(f"Error clearing tasks: {e}")
            raise

# ------------------------------ GLOBAL INSTANCE ------------------------------
turo_service = TuroService()

# ------------------------------ END OF FILE ------------------------------