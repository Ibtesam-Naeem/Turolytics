# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
from typing import Optional, Dict, Any, Sequence, List
from datetime import datetime
from enum import Enum

from core.config.settings import settings
from core.security.session import save_storage_state
from core.database import SessionLocal
from core.database.db_service import DatabaseService
from core.database.models import Trip, Receipt
from sqlalchemy import or_, text

from turo.data.login import complete_turo_login
from turo.data.vehicles import scrape_vehicle_listings
from turo.data.trips import scrape_all_trips
from turo.data.earnings import scrape_earnings_data
from turo.data.ratings import scrape_ratings_data
from turo.data.transactions import scrape_transactions_data
from turo.data.receipts import scrape_receipts_data


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
    TRANSACTIONS = "transactions"
    RECEIPTS = "receipts"
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
            ScrapingType.TRANSACTIONS: scrape_transactions_data,
            ScrapingType.RECEIPTS: scrape_receipts_data,
        }
        self._semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_tasks)
        self._background_tasks: set = set()
        # Exclude ALL from the list of scraper types to run
        self._all_scraper_types = [st for st in self._scrapers.keys() if st != ScrapingType.ALL]
    
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
                    
                    if existing_trip_ids or existing_customer_ids:
                        logger.info(
                            f"Found {len(existing_trip_ids)} existing trips and {len(existing_customer_ids)} existing reviews - "
                            f"Skipping these during scraping"
                        )
                    else:
                        logger.info("No existing trips or reviews found - Scraping all data")
                        
                except Exception as e:
                    logger.warning(f"Error fetching existing IDs: {e}. Scraping all data.")
                    existing_trip_ids = set()
                    existing_customer_ids = set()
                finally:
                    db.close()
                
                login_result = await complete_turo_login(account_id=user_id, email=email, password=password)
                if not login_result:
                    raise RuntimeError("Login failed - unable to authenticate with Turo")
                
                page, context, browser = login_result
                self._update_task_status(task_id, TaskStatus.RUNNING, "Login successful, starting scraping...", scraper_types=[t.value for t in scrapers])
                
                # Check if this is an initial scrape for earnings and transactions
                db_check = SessionLocal()
                try:
                    is_initial_earnings_scrape = not DatabaseService.has_existing_earnings(db_check, user_id)
                    if is_initial_earnings_scrape:
                        logger.info("Initial earnings scrape detected - will scrape multiple years")
                    
                    is_initial_transactions_scrape = not DatabaseService.has_existing_transactions(db_check, user_id)
                    if is_initial_transactions_scrape:
                        logger.info("Initial transactions scrape detected - will scrape all years")
                except Exception as e:
                    logger.warning(f"Error checking existing earnings/transactions: {e}. Assuming regular scrape.")
                    is_initial_earnings_scrape = False
                    is_initial_transactions_scrape = False
                finally:
                    db_check.close()
                
                # Track trip_ids from scraped trips for receipts scraping
                scraped_trip_ids = []
                
                for scraper_type in scrapers:
                    try:
                        logger.info(f"Scraping {scraper_type.value}...")
                        scraper_func = self._scrapers[scraper_type]
                        
                        if scraper_type == ScrapingType.TRIPS:
                            data = await scraper_func(page, existing_trip_ids=existing_trip_ids)
                            # Extract trip_ids from scraped trips for receipts
                            if data and "trips" in data:
                                scraped_trip_ids = [trip.get("trip_id") for trip in data.get("trips", []) if trip.get("trip_id")]
                        elif scraper_type == ScrapingType.REVIEWS:
                            data = await scraper_func(page, existing_customer_ids=existing_customer_ids)
                        elif scraper_type == ScrapingType.EARNINGS:
                            data = await scraper_func(page, is_initial_scrape=is_initial_earnings_scrape)
                        elif scraper_type == ScrapingType.TRANSACTIONS:
                            data = await scraper_func(page, is_initial_scrape=is_initial_transactions_scrape)
                        elif scraper_type == ScrapingType.RECEIPTS:
                            # Use scraped trip_ids if available, otherwise query database for trips without receipts
                            if scraped_trip_ids:
                                data = await scraper_func(page, trip_ids=scraped_trip_ids)
                            else:
                                # Query database for trips without receipts
                                db_receipts = SessionLocal()
                                try:
                                    account = DatabaseService.get_account_by_user_id(db_receipts, user_id)
                                    if account:
                                        trips_with_receipts_subq = db_receipts.query(Receipt.trip_id).filter(
                                            Receipt.account_id == account.id
                                        ).subquery()
                                        
                                        trips = db_receipts.query(Trip).filter(
                                            Trip.account_id == account.id,
                                            ~Trip.id.in_(db_receipts.query(trips_with_receipts_subq.c.trip_id))
                                        ).all()
                                        
                                        trip_ids_from_db = [trip.trip_id for trip in trips if trip.trip_id]
                                        if trip_ids_from_db:
                                            data = await scraper_func(page, trip_ids=trip_ids_from_db)
                                        else:
                                            logger.info("No trips without receipts found in database")
                                            data = None
                                    else:
                                        logger.warning("Account not found for receipts scraping")
                                        data = None
                                except Exception as e:
                                    logger.error(f"Error querying trips for receipts: {e}")
                                    data = None
                                finally:
                                    db_receipts.close()
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
                    db = SessionLocal()
                    try:
                        DatabaseService.save_scraped_data(db, user_id, email, results)
                        logger.info(f"Successfully saved scraped data to database for user {user_id}")
                        
                        if context:
                            await save_storage_state(context, account_id=user_id, email=email)
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
    
    async def scrape_transactions(self, user_id: int, email: str = None, password: str = None) -> str:
        """Scrape transactions only."""
        return await self._scrape(ScrapingType.TRANSACTIONS, user_id, email, password)
    
    async def scrape_receipts(self, user_id: int, email: str = None, password: str = None, trip_ids: List[str] = None) -> str:
        """Scrape receipts for trips.
        
        Args:
            user_id: User ID
            email: Turo email (optional, for login)
            password: Turo password (optional, for login)
            trip_ids: List of trip IDs to scrape receipts for. If None, scrapes receipts for all trips without receipt data.
        """
        task_id = self._generate_task_id(ScrapingType.RECEIPTS, user_id)
        self._update_task_status(
            task_id,
            TaskStatus.PENDING,
            "Queued for execution",
            scraper_types=["receipts"]
        )
        
        task = asyncio.create_task(self._execute_receipt_scraping(user_id, task_id, email, password, trip_ids))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        return task_id
    
    async def _execute_receipt_scraping(self, user_id: int, task_id: str, email: str = None, password: str = None, trip_ids: List[str] = None) -> None:
        """Execute receipt scraping session."""
        async with self._semaphore:
            page, context, browser = None, None, None
            results = {}
            
            try:
                # Get trip IDs if not provided
                if trip_ids is None:
                    db = SessionLocal()
                    try:
                        account = DatabaseService.get_account_by_user_id(db, user_id)
                        if account:
                            # Log which account and Turo email we're using
                            from core.database.models import TuroIntegration
                            turo_integration = db.query(TuroIntegration).filter(
                                TuroIntegration.account_id == account.id
                            ).first()
                            
                            if turo_integration:
                                logger.info(f"Querying trips for Account ID {account.id} (Turolytics email: {account.email}, Turo email: {turo_integration.turo_email})")
                            else:
                                logger.info(f"Querying trips for Account ID {account.id} (Turolytics email: {account.email}, no Turo integration found)")
                            
                            # First, check total trips for this account
                            total_trips = db.query(Trip).filter(Trip.account_id == account.id).count()
                            logger.info(f"Total trips in database for Account ID {account.id}: {total_trips}")
                            
                            # Check how many receipts exist
                            total_receipts = db.query(Receipt).filter(Receipt.account_id == account.id).count()
                            logger.info(f"Total receipts in database for Account ID {account.id}: {total_receipts}")
                            
                            # Get all trips that don't have a receipt record
                            # Match by reservation_id (trip_id in Trip matches reservation_id in Receipt)
                            trips_with_receipts = db.query(Receipt.reservation_id).filter(
                                Receipt.account_id == account.id
                            ).subquery()
                            
                            # If there are no receipts, the subquery will be empty, so we need to handle that
                            trips_query = db.query(Trip).filter(Trip.account_id == account.id)
                            
                            # Only exclude trips with receipts if there are any receipts
                            if total_receipts > 0:
                                trips = trips_query.filter(
                                    ~Trip.trip_id.in_(db.query(trips_with_receipts.c.reservation_id))
                                ).all()
                            else:
                                # No receipts exist, so all trips need receipts
                                trips = trips_query.all()
                            
                            trip_ids = [trip.trip_id for trip in trips if trip.trip_id]
                            logger.info(f"Found {len(trip_ids)} trips without receipt data for Account ID {account.id}")
                            
                            if total_trips > 0 and len(trip_ids) == 0:
                                logger.warning(f"All {total_trips} trips already have receipts, or query issue detected")
                        else:
                            logger.warning(f"Account not found for user {user_id}")
                            trip_ids = []
                    except Exception as e:
                        logger.error(f"Error fetching trip IDs: {e}")
                        trip_ids = []
                    finally:
                        db.close()
                
                if not trip_ids:
                    logger.warning("No trip IDs to scrape receipts for")
                    self._update_task_status(task_id, TaskStatus.COMPLETED, "No trips to scrape receipts for", scraper_types=["receipts"])
                    return
                
                login_result = await complete_turo_login(account_id=user_id, email=email, password=password)
                if not login_result:
                    raise RuntimeError("Login failed - unable to authenticate with Turo")
                
                page, context, browser = login_result
                self._update_task_status(task_id, TaskStatus.RUNNING, f"Login successful, scraping receipts for {len(trip_ids)} trips...", scraper_types=["receipts"])
                
                # Scrape receipts
                data = await scrape_receipts_data(page, trip_ids=trip_ids, batch_size=5)
                
                if data:
                    results["receipts"] = data
                    logger.info(f"Successfully scraped {data.get('total_receipts', 0)} receipts")
                else:
                    logger.warning("No receipt data was scraped")
                
                # Save receipt data
                if results:
                    db = SessionLocal()
                    try:
                        DatabaseService.save_scraped_data(db, user_id, email, results)
                        logger.info(f"Successfully saved receipt data to database for user {user_id}")
                        
                        if context:
                            await save_storage_state(context, account_id=user_id, email=email)
                    except Exception as e:
                        logger.error(f"Error saving receipt data to database: {e}")
                    finally:
                        db.close()
                    
                    self._update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        f"Receipt scraping completed successfully ({data.get('total_receipts', 0) if data else 0} receipts)",
                        {"scraped_data": results},
                        scraper_types=["receipts"]
                    )
                else:
                    self._update_task_status(task_id, TaskStatus.FAILED, "No receipt data scraped", scraper_types=["receipts"])
                    
            except Exception as e:
                logger.error(f"Receipt scraping session failed: {e}")
                self._update_task_status(task_id, TaskStatus.FAILED, f"Session failed: {str(e)}", scraper_types=["receipts"])
            finally:
                if browser:
                    try:
                        await browser.close()
                        logger.info("Browser closed successfully")
                    except Exception as e:
                        logger.warning(f"Error closing browser: {e}")
    
    # ------------------------------ TASK MANAGEMENT ------------------------------
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        return self.active_tasks.get(task_id)

# ------------------------------ END OF FILE ------------------------------