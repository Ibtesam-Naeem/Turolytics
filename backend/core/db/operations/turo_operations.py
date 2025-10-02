# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timezone
import re
from typing import Any, Optional
import logging
# Removed unused import: traceback
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text

from core.config.settings import settings
from core.db.base import Account, Vehicle, Trip, Payout, PayoutItem, Review, PayoutType, VehicleStatus, TripStatus
from core.db.database import get_db_session
from core.utils.data_helpers import parse_amount, extract_vehicle_info

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def parse_turo_date(date_str: str) -> Optional[datetime]:
    """Parse Turo date strings like 'Sep 25', 'Jul 12' into datetime objects.
    
    Args:
        date_str: Date string from Turo (e.g., 'Sep 25', 'Jul 12')
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        match = re.match(r'([A-Za-z]{3})\s+(\d+)', date_str.strip())
        if match:
            month_name, day = match.groups()
            month = month_map.get(month_name)
            if month:
                current_year = datetime.now().year
                return datetime(current_year, month, int(day), tzinfo=timezone.utc)
        
        return None

    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None

# ------------------------------ SESSION MANAGEMENT ------------------------------

@contextmanager
def get_session():
    """Context manager for database sessions with automatic commit/rollback."""
    with get_db_session() as db:
        yield db

def bulk_save_objects(db: Session, objects: list[Any]) -> int:
    """Bulk save objects to database for better performance.
    
    Args:
        db: Database session.
        objects: List of model objects to save.
        
    Returns:
        Number of objects saved.
    """
    if not objects:
        return 0
    
    try:
        db.add_all(objects)
        db.commit()
        return len(objects)
    except Exception as e:
        logger.error(f"Error bulk saving objects: {e}")
        db.rollback()
        raise

# ------------------------------ ACCOUNT OPERATIONS ------------------------------

def get_account_by_email(email: str) -> Optional[Account]:
    """Get account by Turo email.
    
    Args:
        email: Turo account email address.
        
    Returns:
        Account object if found, None otherwise.
    """
    try:
        with get_db_session() as db:
            account = db.query(Account).filter(Account.turo_email == email).first()
            if account:
                # Ensure the account is properly attached to the session
                db.refresh(account)
            return account
    except Exception as e:
        logger.error(f"Error getting account by email {email}: {e}")
        return None

def create_account(email: str, account_name: str = None) -> Optional[int]:
    """Create a new account.
    
    Args:
        email: Turo account email address.
        account_name: Optional account name.
        
    Returns:
        Account ID if created successfully, None otherwise.
    """
    try:
        with get_db_session() as db:
            existing_account = db.query(Account).filter(Account.turo_email == email).first()
            if existing_account:
                logger.info(f"Account with email {email} already exists")
                return existing_account.id
            
            account = Account(
                turo_email=email,
                account_name=account_name or "",
                is_active=True
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            
            account_id = account.id
            logger.info(f"Created new account for {email} with ID {account_id}")
            return account_id
    except Exception as e:
        logger.error(f"Error creating account for {email}: {e}")
        return None

def get_or_create_account(email: str, account_name: str = None) -> Optional[int]:
    """Get existing account or create new one.
    
    Args:
        email: Turo account email address.
        account_name: Optional account name.
        
    Returns:
        Account ID if found or created successfully, None otherwise.
    """
    try:
        account = get_account_by_email(email)
        if account:
            return account.id
        
        return create_account(email, account_name)
    except Exception as e:
        logger.error(f"Error getting or creating account for {email}: {e}")
        return None

# ------------------------------ VEHICLE OPERATIONS ------------------------------

def _normalize_vehicle_status(status: str) -> VehicleStatus:
    """Normalize vehicle status string to VehicleStatus enum.
    
    Args:
        status: Status string from scraper (e.g., 'Listed', 'Snoozed')
        
    Returns:
        VehicleStatus enum value
    """
    if not status:
        return VehicleStatus.LISTED
    
    status_map = {
        'listed': VehicleStatus.LISTED,
        'snoozed': VehicleStatus.SNOOZED,
        'unavailable': VehicleStatus.UNAVAILABLE,
        'maintenance': VehicleStatus.MAINTENANCE,
        'active': VehicleStatus.LISTED,
        'inactive': VehicleStatus.SNOOZED,
        'disabled': VehicleStatus.UNAVAILABLE
    }
    
    normalized = status.lower().strip()
    if normalized in status_map:
        return status_map[normalized]
    
    logger.warning(f"Unknown vehicle status '{status}', defaulting to LISTED")
    return VehicleStatus.LISTED

def _parse_vehicle_name(vehicle_name: str) -> tuple[str, str, int]:
    """Parse vehicle name to extract make, model, and year using data_helpers."""
    if not vehicle_name:
        return None, None, None
    
    info = extract_vehicle_info(vehicle_name)
    return info.get('make'), info.get('model'), info.get('year')

def save_vehicles_data(account_id: int, vehicles_data: dict[str, Any]) -> int:
    """Save vehicles data to database.
    
    Args:
        account_id: Account ID to save vehicles for.
        vehicles_data: Dictionary containing vehicle data from scraper.
        
    Returns:
        Number of vehicles saved.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    try:
        with get_db_session() as db:
            vehicles_saved = 0
            
            vehicles_list = []
            if 'vehicles' in vehicles_data:
                vehicles_list = vehicles_data['vehicles']
            elif 'listings' in vehicles_data and 'vehicles' in vehicles_data['listings']:
                vehicles_list = vehicles_data['listings']['vehicles']
            
            for vehicle_data in vehicles_list:
                    try:
                        vehicle_name = vehicle_data.get('name', '')
                        make, model, year = _parse_vehicle_name(vehicle_name)
                        
                        vehicle = Vehicle(
                            account_id=account_id,
                            turo_vehicle_id=vehicle_data.get('vehicle_id'),
                            make=make,
                            model=model,
                            year=year,
                            status=_normalize_vehicle_status(vehicle_data.get('status', 'Listed')),
                            rating=vehicle_data.get('rating'),
                            trip_count=vehicle_data.get('trip_count', 0)
                        )
                        db.add(vehicle)
                        vehicles_saved += 1

                    except Exception as e:
                        logger.warning(f"Error saving vehicle {vehicle_data.get('vehicle_id')}: {e}")
                        continue
            
            db.commit()
            logger.info(f"Saved {vehicles_saved} vehicles for account {account_id}")
            return vehicles_saved
            
    except Exception as e:
        logger.error(f"Error saving vehicles data: {e}")
        raise

# ------------------------------ TRIP OPERATIONS ------------------------------

def _normalize_trip_status(status: str) -> TripStatus:
    """Normalize trip status string to TripStatus enum.
    
    Args:
        status: Status string from scraper (e.g., 'COMPLETED', 'CANCELLED')
        
    Returns:
        TripStatus enum value
        
    Raises:
        ValueError: If status cannot be normalized
    """
    if not status:
        return TripStatus.PENDING
    
    normalized = status.lower().strip()
    
    status_map = {
        'completed': TripStatus.COMPLETED,
        'cancelled': TripStatus.CANCELLED,
        'canceled': TripStatus.CANCELLED,  # Handle both spellings
        'booked': TripStatus.BOOKED,
        'in_progress': TripStatus.IN_PROGRESS,
        'pending': TripStatus.PENDING,
        'active': TripStatus.IN_PROGRESS,
        'finished': TripStatus.COMPLETED,
        'done': TripStatus.COMPLETED
    }
    
    if normalized in status_map:
        return status_map[normalized]
    
    logger.warning(f"Unknown trip status '{status}', defaulting to PENDING")
    return TripStatus.PENDING

def _upsert_trip(db: Session, account_id: int, trip_data: dict) -> str:
    """Upsert (insert or update) a trip record.
    
    Args:
        db: Database session
        account_id: Account ID
        trip_data: Trip data dictionary
        
    Returns:
        "created", "updated", or False if failed
    """
    try:
        turo_trip_id = trip_data.get('trip_id')
        if not turo_trip_id:
            logger.warning("Trip data missing turo_trip_id, skipping")
            return False
        
        existing_trip = db.query(Trip).filter(
            Trip.account_id == account_id,
            Trip.turo_trip_id == turo_trip_id
        ).first()
        
        if existing_trip:
            existing_trip.vehicle_id = trip_data.get('vehicle_id')
            existing_trip.customer_name = trip_data.get('guest_name')
            existing_trip.status = _normalize_trip_status(trip_data.get('status'))
            existing_trip.start_date = parse_turo_date(trip_data.get('start_date'))
            existing_trip.end_date = parse_turo_date(trip_data.get('end_date'))
            existing_trip.price_total = parse_amount(trip_data.get('total_amount'))
            existing_trip.earnings = parse_amount(trip_data.get('trip_earnings'))
            existing_trip.updated_at = datetime.now(timezone.utc)
            logger.debug(f"Updated existing trip {turo_trip_id}")
            return "updated"
        else:
            trip = Trip(
                account_id=account_id,
                turo_trip_id=turo_trip_id,
                vehicle_id=trip_data.get('vehicle_id'),
                customer_name=trip_data.get('guest_name'),
                status=_normalize_trip_status(trip_data.get('status')),
                start_date=parse_turo_date(trip_data.get('start_date')),
                end_date=parse_turo_date(trip_data.get('end_date')),
                price_total=parse_amount(trip_data.get('total_amount')),
                earnings=parse_amount(trip_data.get('trip_earnings'))
            )
            db.add(trip)
            logger.debug(f"Created new trip {turo_trip_id}")
            return "created"
        
    except Exception as e:
        logger.warning(f"Error upserting trip {trip_data.get('trip_id')}: {e}")
        return False

def save_trips_data(account_id: int, trips_data: dict[str, Any]) -> int:
    """Save trips data to database using upsert logic.
    
    Args:
        account_id: Account ID to save trips for.
        trips_data: Dictionary containing trip data from scraper.
        
    Returns:
        Number of trips processed successfully.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    try:
        with get_db_session() as db:
            trips_processed = 0
            trips_created = 0
            trips_updated = 0
            
            if 'booked_trips' in trips_data and 'trips' in trips_data['booked_trips']:
                for trip_data in trips_data['booked_trips']['trips']:
                    result = _upsert_trip(db, account_id, trip_data)
                    if result:
                        trips_processed += 1
                        if result == "created":
                            trips_created += 1
                        elif result == "updated":
                            trips_updated += 1
            
            if 'trip_history' in trips_data and 'trips' in trips_data['trip_history']:
                for trip_data in trips_data['trip_history']['trips']:
                    result = _upsert_trip(db, account_id, trip_data)
                    if result:
                        trips_processed += 1
                        if result == "created":
                            trips_created += 1
                        elif result == "updated":
                            trips_updated += 1
            
            db.commit()
            logger.info(f"Processed {trips_processed} trips for account {account_id} (Created: {trips_created}, Updated: {trips_updated})")
            return trips_processed
            
    except Exception as e:
        logger.error(f"Error saving trips data: {e}")
        db.rollback()
        raise

# ------------------------------ EARNINGS OPERATIONS ------------------------------

def save_earnings_data(account_id: int, earnings_data: dict[str, Any]) -> int:
    """Save earnings data to database.
    
    Args:
        account_id: Account ID to save earnings for.
        earnings_data: Dictionary containing earnings data from scraper.
        
    Returns:
        Number of earnings items saved.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    try:
        with get_db_session() as db:
            earnings_saved = 0
            
            if 'earnings' in earnings_data and 'earnings_breakdown' in earnings_data['earnings']:
                for earning_data in earnings_data['earnings']['earnings_breakdown']:
                    try:
                        payout = Payout(
                            account_id=account_id,
                            turo_payout_id=earning_data.get('payout_id'),
                            amount=parse_amount(earning_data.get('amount')),
                            payout_at=parse_turo_date(earning_data.get('date'))
                        )
                        db.add(payout)
                        earnings_saved += 1
                    except Exception as e:
                        logger.warning(f"Error saving earning {earning_data.get('id')}: {e}")
                        continue
            
            db.commit()
            logger.info(f"Saved {earnings_saved} earnings for account {account_id}")
            return earnings_saved
            
    except Exception as e:
        logger.error(f"Error saving earnings data: {e}")
        raise

# ------------------------------ REVIEW OPERATIONS ------------------------------

def save_reviews_data(account_id: int, reviews_data: dict[str, Any]) -> int:
    """Save reviews data to database.
    
    Args:
        account_id: Account ID to save reviews for.
        reviews_data: Dictionary containing review data from scraper.
        
    Returns:
        Number of reviews saved.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    try:
        with get_db_session() as db:
            reviews_saved = 0
            
            if 'ratings' in reviews_data and 'reviews' in reviews_data['ratings']:
                for review_data in reviews_data['ratings']['reviews']:
                    try:
                        review = Review(
                            account_id=account_id,
                            turo_review_id=review_data.get('id'),
                            customer_name=review_data.get('guest_name'),
                            rating=review_data.get('rating'),
                            review_text=review_data.get('comment'),
                            date=parse_turo_date(review_data.get('date'))
                        )
                        db.add(review)
                        reviews_saved += 1
                    except Exception as e:
                        logger.warning(f"Error saving review {review_data.get('id')}: {e}")
                        continue
            
            db.commit()
            logger.info(f"Saved {reviews_saved} reviews for account {account_id}")
            return reviews_saved
            
    except Exception as e:
        logger.error(f"Error saving reviews data: {e}")
        raise

# ------------------------------ MAIN OPERATIONS ------------------------------

def save_scraped_data(account_id: int, scraped_data: dict[str, Any]) -> dict[str, int]:
    """Save all scraped data to database.
    
    Args:
        account_id: Account ID to save data for.
        scraped_data: Dictionary containing all scraped data (vehicles, trips, earnings, ratings).
        
    Returns:
        Dictionary with count of saved records per data type.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    results = {
        'vehicles': 0,
        'trips': 0,
        'earnings': 0,
        'reviews': 0
    }
    
    try:
        if 'vehicles' in scraped_data:
            results['vehicles'] = save_vehicles_data(account_id, scraped_data['vehicles'])
        
        if 'trips' in scraped_data:
            results['trips'] = save_trips_data(account_id, scraped_data['trips'])
        
        if 'earnings' in scraped_data:
            results['earnings'] = save_earnings_data(account_id, scraped_data['earnings'])
        
        if 'ratings' in scraped_data:
            results['reviews'] = save_reviews_data(account_id, scraped_data['ratings'])
        
        logger.info(f"Saved scraped data: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error saving scraped data: {e}")
        raise

def get_database_stats(account_id: int) -> dict:
    """Get database statistics for an account.
    
    Args:
        account_id: Account ID to get stats for.
        
    Returns:
        Dictionary with count of records per data type.
    """
    try:
        with get_db_session() as db:
            stats = {
                'vehicles': db.query(Vehicle).filter(Vehicle.account_id == account_id).count(),
                'trips': db.query(Trip).filter(Trip.account_id == account_id).count(),
                'earnings': db.query(Payout).filter(Payout.account_id == account_id).count(),
                'reviews': db.query(Review).filter(Review.account_id == account_id).count()
            }
            return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}

# ------------------------------ END OF FILE ------------------------------