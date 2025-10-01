# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timezone
import re
from typing import Any, Optional
import logging
import traceback
import hashlib
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text

from ..config import SessionLocal
from ..models import Account, Vehicle, Trip, Payout, PayoutItem, Review, PayoutType, VehicleStatus, TripStatus
from utils.data_helpers import parse_amount, extract_vehicle_info

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
    db = SessionLocal()

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

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
        db.bulk_save_objects(objects)
        return len(objects)

    except Exception as e:
        logger.error(f"Error in bulk save: {e}")
        logger.debug(traceback.format_exc())
        raise

# ------------------------------ ACCOUNT OPERATIONS ------------------------------

def get_account_by_email(email: str) -> Optional[Account]:
    """Get account by Turo email.
    
    Args:
        email: Turo account email address.
        
    Returns:
        Account object if found, None otherwise.
    """
    db = SessionLocal()

    try:
        return db.query(Account).filter(Account.turo_email == email).first()
    finally:
        db.close()

def get_or_create_account(email: str, account_name: str = None) -> Account:
    """Get existing account or create new one.
    
    Args:
        email: Turo account email address.
        account_name: Optional display name for the account.
        
    Returns:
        Account object (existing or newly created).
        
    Raises:
        Exception: If database error occurs during account creation.
    """
    db = SessionLocal()

    try:
        account = get_account_by_email(email)
        if not account:
            account = Account(
                turo_email=email,
                account_name=account_name or email
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"Created new account for {email}")
        return account

    except Exception as e:
        logger.error(f"Error getting/creating account: {e}")
        db.rollback()
        raise

    finally:
        db.close()

# ------------------------------ VEHICLE OPERATIONS ------------------------------

def get_vehicle_by_turo_id(account_id: int, turo_vehicle_id: str) -> Optional[Vehicle]:
    """Get vehicle by Turo ID.
    
    Args:
        account_id: Account ID to search within.
        turo_vehicle_id: Turo's vehicle ID.
        
    Returns:
        Vehicle object if found, None otherwise.
    """
    db = SessionLocal()
    try:
        return db.query(Vehicle).filter(
            and_(Vehicle.account_id == account_id,
                 Vehicle.turo_vehicle_id == turo_vehicle_id)
        ).first()
    finally:
        db.close()

def get_vehicles_by_account(account_id: int) -> list[Vehicle]:
    """Get all vehicles for an account.
    
    Args:
        account_id: Account ID to get vehicles for.
        
    Returns:
        List of Vehicle objects for the account.
    """
    db = SessionLocal()
    try:
        return db.query(Vehicle).filter(Vehicle.account_id == account_id).all()
    finally:
        db.close()

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
    db = SessionLocal()
    vehicles_saved = 0
    
    try:
        listings = vehicles_data.get('listings', {})
        vehicles = listings.get('vehicles', [])
        
        for vehicle_data in vehicles:
            turo_vehicle_id = vehicle_data.get('vehicle_id')
            if not turo_vehicle_id:
                vehicle_name = vehicle_data.get('name', 'Unknown')
                turo_vehicle_id = f"generated_{hash(vehicle_name) % 1000000}"
                
            status_str = vehicle_data.get('status')
            status_enum = None
            if status_str:
                try:
                    status_mapping = {
                        'Listed': VehicleStatus.LISTED,
                        'Snoozed': VehicleStatus.SNOOZED,
                        'Unavailable': VehicleStatus.UNAVAILABLE,
                        'Maintenance': VehicleStatus.MAINTENANCE
                    }
                    status_enum = status_mapping.get(status_str)
                except (ValueError, KeyError):
                    logger.warning(f"Unknown vehicle status: {status_str}")
            
            vehicle = db.query(Vehicle).filter(
                and_(Vehicle.account_id == account_id, 
                     Vehicle.turo_vehicle_id == turo_vehicle_id)
            ).first()
            
            if not vehicle:
                vehicle = Vehicle(account_id=account_id)
                db.add(vehicle)
            
            vehicle.turo_vehicle_id = turo_vehicle_id
            vehicle.name = vehicle_data.get('name')
            vehicle.status = status_enum
            vehicle.license_plate = vehicle_data.get('license_plate')
            vehicle.trim = vehicle_data.get('trim')
            vehicle.rating = vehicle_data.get('rating')
            vehicle.trip_count = vehicle_data.get('trip_count')
            
            image_data = vehicle_data.get('image', {})
            if image_data:
                vehicle.image_url = image_data.get('url')
                vehicle.image_alt = image_data.get('alt')
            
            if vehicle.name:
                vehicle_info = extract_vehicle_info(vehicle.name)
                vehicle.year = vehicle_info['year']
                vehicle.make = vehicle_info['make']
                vehicle.model = vehicle_info['model']
            
            vehicle.last_seen_at = datetime.now(timezone.utc)
            vehicle.scraped_at = datetime.now(timezone.utc)
            
            vehicles_saved += 1
        
        db.commit()
        logger.info(f"Saved {vehicles_saved} vehicles for account {account_id}")
        return vehicles_saved
        
    except Exception as e:
        logger.error(f"Error saving vehicles data: {e}")
        db.rollback()
        raise

    finally:
        db.close()

# ------------------------------ TRIP OPERATIONS ------------------------------

def get_trip_by_turo_id(account_id: int, turo_trip_id: str) -> Optional[Trip]:
    """Get trip by Turo ID.
    
    Args:
        account_id: Account ID to search within.
        turo_trip_id: Turo's trip ID.
        
    Returns:
        Trip object if found, None otherwise.
    """
    db = SessionLocal()
    try:
        return db.query(Trip).filter(
            and_(Trip.account_id == account_id,
                 Trip.turo_trip_id == turo_trip_id)
        ).first()
    finally:
        db.close()

def get_trips_by_account(account_id: int, limit: int = 100) -> list[Trip]:
    """Get recent trips for an account.
    
    Args:
        account_id: Account ID to get trips for.
        limit: Maximum number of trips to return.
        
    Returns:
        List of Trip objects for the account.
    """
    db = SessionLocal()
    try:
        return db.query(Trip).filter(
            Trip.account_id == account_id
        ).order_by(desc(Trip.created_at)).limit(limit).all()
    finally:
        db.close()

def get_trips_by_vehicle(vehicle_id: int) -> list[Trip]:
    """Get trips for a specific vehicle.
    
    Args:
        vehicle_id: Vehicle ID to get trips for.
        
    Returns:
        List of Trip objects for the vehicle.
    """
    db = SessionLocal()
    try:
        return db.query(Trip).filter(Trip.vehicle_id == vehicle_id).all()
    finally:
        db.close()

def save_trips_data(account_id: int, trips_data: dict[str, Any]) -> int:
    """Save trips data to database.
    
    Args:
        account_id: Account ID to save trips for.
        trips_data: Dictionary containing trip data from scraper.
        
    Returns:
        Number of trips saved.
        
    Raises:
        Exception: If database error occurs during save operation.
    """
    db = SessionLocal()
    trips_saved = 0
    
    try:
        booked_trips = trips_data.get('booked_trips', {}).get('trips', [])
        for trip_data in booked_trips:
            trips_saved += _save_single_trip(db, account_id, trip_data, "booked")
        
        history_trips = trips_data.get('trip_history', {}).get('trips', [])
        for trip_data in history_trips:
            trips_saved += _save_single_trip(db, account_id, trip_data, "history")
        
        db.commit()
        logger.info(f"Saved {trips_saved} trips for account {account_id}")
        return trips_saved
        
    except Exception as e:
        logger.error(f"Error saving trips data: {e}")
        db.rollback()
        raise

    finally:
        db.close()

def _save_single_trip(db: Session, account_id: int, trip_data: dict[str, Any], trip_type: str) -> int:
    """Save a single trip to database.
    
    Args:
        db: Database session.
        account_id: Account ID to save trip for.
        trip_data: Dictionary containing trip data.
        trip_type: Type of trip (booked, history).
        
    Returns:
        1 if trip saved successfully, 0 otherwise.
    """
    turo_trip_id = trip_data.get('trip_id')
    if not turo_trip_id:
        return 0
    
    # Find or create trip
    trip = db.query(Trip).filter(
        and_(Trip.account_id == account_id, 
             Trip.turo_trip_id == turo_trip_id)
    ).first()
    
    if not trip:
        trip = Trip(account_id=account_id)
        db.add(trip)
    
    trip.turo_trip_id = turo_trip_id
    trip.turo_trip_url = trip_data.get('trip_url')
    trip.trip_dates = trip_data.get('trip_dates')
    trip.customer_name = trip_data.get('customer_name')
    trip.customer_id = trip_data.get('customer_id')
    trip.customer_info = trip_data.get('customer_info')
    trip.customer_found = trip_data.get('customer_found', False)
    
    status_str = trip_data.get('status')
    status_enum = None
    if status_str:
        try:
            status_mapping = {
                'booked': TripStatus.BOOKED,
                'completed': TripStatus.COMPLETED,
                'cancelled': TripStatus.CANCELLED,
                'in_progress': TripStatus.IN_PROGRESS,
                'pending': TripStatus.PENDING
            }
            status_enum = status_mapping.get(status_str.lower())

        except (ValueError, KeyError):
            logger.warning(f"Unknown trip status: {status_str}")
    
    trip.status = status_enum
    trip.cancellation_info = trip_data.get('cancellation_info')
    trip.cancelled_by = trip_data.get('cancelled_by')
    
    cancelled_date_str = trip_data.get('cancelled_date')
    trip.cancelled_date = parse_turo_date(cancelled_date_str) if cancelled_date_str else None
    trip.vehicle_image = trip_data.get('vehicle_image')
    trip.customer_profile_image = trip_data.get('customer_profile_image')
    trip.has_customer_photo = trip_data.get('has_customer_photo', False)
    trip.scraped_at = datetime.now(timezone.utc)
    
    vehicle_name = trip_data.get('vehicle')

    if vehicle_name:
        vehicle = db.query(Vehicle).filter(
            and_(Vehicle.account_id == account_id,
                 Vehicle.name == vehicle_name)
        ).first()
        if vehicle:
            trip.vehicle_id = vehicle.id
    
    return 1

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
    items_saved = 0
    
    try:
        with get_session() as db:
            earnings = earnings_data.get('earnings', {})
            payout_items = []
            
            breakdown = earnings.get('earnings_breakdown', [])
            for item_data in breakdown:
                # Handle payout type conversion with fallback
                payout_type = None
                type_str = item_data.get('type')
                if type_str:
                    try:
                        payout_type = PayoutType(type_str)

                    except ValueError:
                        type_mapping = {
                            'Upcoming earnings': PayoutType.UPCOMING_EARNINGS,
                            'Trip earnings': PayoutType.TRIP_EARNINGS,
                            'Reimbursements': PayoutType.REIMBURSEMENTS,
                            'Vehicle earnings': PayoutType.VEHICLE_EARNINGS,
                            'Bonus': PayoutType.BONUS,
                            'Refund': PayoutType.REFUND
                        }
                        payout_type = type_mapping.get(type_str)
                        if not payout_type:
                            logger.warning(f"Unknown payout type: {type_str}")
                
                payout_item = PayoutItem(
                    account_id=account_id,
                    type=payout_type,
                    amount=parse_amount(item_data.get('amount')),
                    description=item_data.get('description'),
                    scraped_at=datetime.now(timezone.utc)
                )
                payout_items.append(payout_item)
            
            vehicle_earnings = earnings.get('vehicle_earnings', [])
            for vehicle_data in vehicle_earnings:
                payout_item = PayoutItem(
                    account_id=account_id,
                    type=PayoutType.VEHICLE_EARNINGS,
                    amount=parse_amount(vehicle_data.get('earnings_amount')),
                    description=f"Earnings for {vehicle_data.get('vehicle_name')}",
                    scraped_at=datetime.now(timezone.utc)
                )
                payout_items.append(payout_item)
            
            items_saved = bulk_save_objects(db, payout_items)
            
        logger.info(f"Saved {items_saved} earnings items for account {account_id}")
        return items_saved
        
    except Exception as e:
        logger.error(f"Error saving earnings data: {e}")
        logger.debug(traceback.format_exc())
        raise

# ------------------------------ REVIEW OPERATIONS ------------------------------

def get_reviews_by_account(account_id: int, limit: int = 100) -> list[Review]:
    """Get recent reviews for an account.
    
    Args:
        account_id: Account ID to get reviews for.
        limit: Maximum number of reviews to return.
        
    Returns:
        List of Review objects for the account.
    """
    db = SessionLocal()
    try:
        return db.query(Review).filter(
            Review.account_id == account_id
        ).order_by(desc(Review.created_at)).limit(limit).all()
    finally:
        db.close()

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
    db = SessionLocal()
    reviews_saved = 0
    
    try:
        ratings = reviews_data.get('ratings', {})
        reviews = ratings.get('reviews', [])
        
        for review_data in reviews:
            customer_id = review_data.get('customer_id')
            trip_id = review_data.get('trip_id')
            if not customer_id:
                continue
            
            review_id_data = f"{customer_id}_{trip_id or 'unknown'}"
            turo_review_id = hashlib.md5(review_id_data.encode()).hexdigest()[:16]
            
            review = db.query(Review).filter(
                and_(Review.account_id == account_id,
                     Review.turo_review_id == turo_review_id)
            ).first()
            
            if not review:
                review = Review(account_id=account_id)
                db.add(review)
            
            review.turo_review_id = turo_review_id
            review.customer_name = review_data.get('customer_name')
            review.customer_id = review_data.get('customer_id')
            review.customer_image_url = review_data.get('customer_image_url')
            review.customer_image_alt = review_data.get('customer_image_alt')
            review.rating = review_data.get('rating')
            review.date = review_data.get('date')
            review.vehicle_info = review_data.get('vehicle_info')
            review.review_text = review_data.get('review_text')
            review.areas_of_improvement = review_data.get('areas_of_improvement', [])
            review.host_response = review_data.get('host_response')
            review.has_host_response = review_data.get('has_host_response', False)
            review.scraped_at = datetime.utcnow()
            
            reviews_saved += 1
        
        db.commit()
        logger.info(f"Saved {reviews_saved} reviews for account {account_id}")
        return reviews_saved
        
    except Exception as e:
        logger.error(f"Error saving reviews data: {e}")
        logger.debug(traceback.format_exc())
        db.rollback()
        raise
    
    finally:
        db.close()

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
    db = SessionLocal()
    try:
        vehicles_count = db.query(Vehicle).filter(Vehicle.account_id == account_id).count()
        trips_count = db.query(Trip).filter(Trip.account_id == account_id).count()
        reviews_count = db.query(Review).filter(Review.account_id == account_id).count()
        
        return {
            'vehicles': vehicles_count,
            'trips': trips_count,
            'reviews': reviews_count
        }
    finally:
        db.close()

# ------------------------------ END OF FILE ------------------------------
