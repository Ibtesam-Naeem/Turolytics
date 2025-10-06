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
        with get_db_session() as db:
            # First try to get existing account
            account = db.query(Account).filter(Account.turo_email == email).first()
            if account:
                return account.id
            
            # Create new account if not found
            new_account = Account(
                turo_email=email,
                account_name=account_name or "",
                is_active=True
            )
            db.add(new_account)
            db.commit()
            db.refresh(new_account)
            
            logger.info(f"Created new account for {email} with ID {new_account.id}")
            return new_account.id
            
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
        
        # Parse trip dates from the trip_dates field
        start_date = None
        end_date = None
        trip_dates = trip_data.get('trip_dates', '')
        if trip_dates:
            # Clean up the trip_dates string first
            cleaned_dates = trip_dates.strip()
            
            # Extract dates from strings like "Oct 1 - Oct 3" or "Sep 25 - Sep 27"
            date_match = re.search(r'([A-Za-z]{3})\s+(\d+)\s*-\s*([A-Za-z]{3})\s+(\d+)', cleaned_dates)
            if date_match:
                start_month, start_day, end_month, end_day = date_match.groups()
                start_date = parse_turo_date(f"{start_month} {start_day}")
                end_date = parse_turo_date(f"{end_month} {end_day}")
            else:
                # Try alternative patterns like "Oct 1 - Oct 3Hyundai Elantra 2017"
                date_match = re.search(r'([A-Za-z]{3})\s+(\d+)\s*-\s*([A-Za-z]{3})\s+(\d+)([A-Za-z0-9\s]+)', cleaned_dates)
                if date_match:
                    start_month, start_day, end_month, end_day, extra = date_match.groups()
                    start_date = parse_turo_date(f"{start_month} {start_day}")
                    end_date = parse_turo_date(f"{end_month} {end_day}")
        
        # Extract customer name from customer_info or customer_name
        customer_name = trip_data.get('customer_name') or trip_data.get('customer_info', '')
        if customer_name and '#' in customer_name:
            customer_name = customer_name.split('#')[0].strip()
        
        # Extract price and earnings from trip data
        price_total = None
        earnings = None
        
        # Look for price patterns in the raw text or specific fields
        raw_text = trip_data.get('raw_card_text', '')
        if raw_text:
            # Look for price patterns like "$45.00" or "$100"
            price_match = re.search(r'\$(\d+\.?\d*)', raw_text)
            if price_match:
                price_total = float(price_match.group(1))
                # For now, assume earnings is same as price (can be refined later)
                earnings = price_total
        
        # Extract vehicle info from vehicle field and match to actual vehicle
        vehicle_info = trip_data.get('vehicle', '')
        vehicle_id = None
        if vehicle_info:
            # Try to find matching vehicle in database based on vehicle info
            # Look for patterns like "Hyundai Elantra 2017" in the vehicle info
            vehicle_match = None
            if 'Hyundai Elantra' in vehicle_info:
                vehicle_match = db.query(Vehicle).filter(
                    Vehicle.account_id == account_id,
                    Vehicle.make == 'Hyundai',
                    Vehicle.model == 'Elantra'
                ).first()
            elif 'Audi Q7' in vehicle_info:
                vehicle_match = db.query(Vehicle).filter(
                    Vehicle.account_id == account_id,
                    Vehicle.make == 'Audi',
                    Vehicle.model == 'Q7'
                ).first()
            
            if vehicle_match:
                vehicle_id = vehicle_match.id
            else:
                # If no match found, use None (trip will be saved without vehicle_id)
                vehicle_id = None
        
        existing_trip = db.query(Trip).filter(
            Trip.account_id == account_id,
            Trip.turo_trip_id == turo_trip_id
        ).first()
        
        if existing_trip:
            existing_trip.turo_trip_url = trip_data.get('trip_url')
            existing_trip.vehicle_id = vehicle_id
            existing_trip.trip_dates = trip_dates
            existing_trip.start_date = start_date
            existing_trip.end_date = end_date
            existing_trip.customer_name = customer_name
            existing_trip.customer_id = trip_data.get('customer_id')
            existing_trip.customer_info = trip_data.get('customer_info')
            existing_trip.customer_found = trip_data.get('customer_found', False)
            existing_trip.status = _normalize_trip_status(trip_data.get('status'))
            existing_trip.cancellation_info = trip_data.get('cancellation_info')
            existing_trip.cancelled_by = trip_data.get('cancelled_by')
            existing_trip.cancelled_date = parse_turo_date(trip_data.get('cancelled_date'))
            existing_trip.vehicle_image = trip_data.get('vehicle_image')
            existing_trip.customer_profile_image = trip_data.get('customer_profile_image')
            existing_trip.has_customer_photo = trip_data.get('has_customer_photo', False)
            existing_trip.price_total = price_total
            existing_trip.earnings = earnings
            existing_trip.updated_at = datetime.now(timezone.utc)
            logger.debug(f"Updated existing trip {turo_trip_id}")
            return "updated"
        else:
            trip = Trip(
                account_id=account_id,
                turo_trip_id=turo_trip_id,
                turo_trip_url=trip_data.get('trip_url'),
                vehicle_id=vehicle_id,
                trip_dates=trip_dates,
                start_date=start_date,
                end_date=end_date,
                customer_name=customer_name,
                customer_id=trip_data.get('customer_id'),
                customer_info=trip_data.get('customer_info'),
                customer_found=trip_data.get('customer_found', False),
                status=_normalize_trip_status(trip_data.get('status')),
                cancellation_info=trip_data.get('cancellation_info'),
                cancelled_by=trip_data.get('cancelled_by'),
                cancelled_date=parse_turo_date(trip_data.get('cancelled_date')),
                vehicle_image=trip_data.get('vehicle_image'),
                customer_profile_image=trip_data.get('customer_profile_image'),
                has_customer_photo=trip_data.get('has_customer_photo', False),
                price_total=price_total,
                earnings=earnings
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
            
            # Process earnings breakdown from the scraped data
            if 'earnings' in earnings_data and 'earnings_breakdown' in earnings_data['earnings']:
                for earning_data in earnings_data['earnings']['earnings_breakdown']:
                    try:
                        # Extract amount from strings like "$835" or "$69"
                        amount_str = earning_data.get('amount', '')
                        amount = parse_amount(amount_str)
                        
                        # Create a unique payout ID based on type and amount
                        payout_type = earning_data.get('type', 'Unknown')
                        payout_id = f"{payout_type}_{amount}_{account_id}" if amount else f"{payout_type}_{account_id}"
                        
                        # Truncate reference to fit database field (255 chars max)
                        reference = earning_data.get('description', '')
                        if len(reference) > 255:
                            reference = reference[:252] + "..."
                        
                        # Check if payout already exists
                        existing_payout = db.query(Payout).filter(
                            Payout.account_id == account_id,
                            Payout.turo_payout_id == payout_id
                        ).first()
                        
                        if existing_payout:
                            # Update existing payout
                            existing_payout.amount = amount
                            existing_payout.method = payout_type
                            existing_payout.reference = reference
                            existing_payout.updated_at = datetime.now(timezone.utc)
                            logger.debug(f"Updated existing payout: {payout_id}")
                        else:
                            # Create new payout
                            payout = Payout(
                                account_id=account_id,
                                turo_payout_id=payout_id,
                                amount=amount,
                                method=payout_type,  # Use type as method
                                reference=reference,
                                payout_at=datetime.now(timezone.utc)  # Use current time since no specific date
                            )
                            db.add(payout)
                            logger.debug(f"Created new payout: {payout_id}")
                        
                        earnings_saved += 1
                    except Exception as e:
                        logger.warning(f"Error saving earning {earning_data.get('type')}: {e}")
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
            
            # Process reviews from the scraped data structure
            logger.info(f"Processing reviews data: {reviews_data}")
            if 'ratings' in reviews_data and 'reviews' in reviews_data['ratings']:
                logger.info(f"Found {len(reviews_data['ratings']['reviews'])} reviews to process")
                for i, review_data in enumerate(reviews_data['ratings']['reviews']):
                    logger.info(f"Processing review {i+1}: {review_data}")
                    try:
                        # Extract customer name directly from the review data
                        customer_name = review_data.get('customer_name')
                        if not customer_name or customer_name == 'Unknown':
                            # Try to extract from vehicle_info field as fallback
                            vehicle_info = review_data.get('vehicle_info', '')
                            if vehicle_info and '•' in vehicle_info:
                                customer_name = vehicle_info.split('•')[0].strip()
                        
                        # Extract date from the review data
                        review_date = None
                        date_str = review_data.get('date')
                        if date_str:
                            # Parse dates like "October 3, 2025" or "September 25, 2025"
                            date_match = re.search(r'([A-Za-z]+)\s+(\d+),\s+(\d{4})', date_str)
                            if date_match:
                                month_name, day, year = date_match.groups()
                                month_map = {
                                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                                }
                                month = month_map.get(month_name)
                                if month:
                                    review_date = datetime(int(year), month, int(day), tzinfo=timezone.utc)
                        
                        # Fallback: try to extract from vehicle_info field
                        if not review_date:
                            vehicle_info = review_data.get('vehicle_info', '')
                            if vehicle_info and '•' in vehicle_info:
                                date_part = vehicle_info.split('•')[1].strip()
                                date_match = re.search(r'([A-Za-z]+)\s+(\d+),\s+(\d{4})', date_part)
                                if date_match:
                                    month_name, day, year = date_match.groups()
                                    month_map = {
                                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                                    }
                                    month = month_map.get(month_name)
                                    if month:
                                        review_date = datetime(int(year), month, int(day), tzinfo=timezone.utc)
                        
                        # Create unique review ID
                        review_id = review_data.get('customer_id') or f"review_{account_id}_{reviews_saved}"
                        
                        # Extract areas of improvement
                        areas_of_improvement = review_data.get('areas_of_improvement', [])
                        if isinstance(areas_of_improvement, list):
                            areas_str = ', '.join(areas_of_improvement)
                        else:
                            areas_str = str(areas_of_improvement) if areas_of_improvement else None
                        
                        # Check if review already exists
                        existing_review = db.query(Review).filter(
                            Review.account_id == account_id,
                            Review.turo_review_id == review_id
                        ).first()
                        
                        if existing_review:
                            # Update existing review
                            existing_review.customer_name = customer_name
                            existing_review.customer_id = review_data.get('customer_id')
                            existing_review.rating = review_data.get('rating')
                            existing_review.date = review_date
                            existing_review.vehicle_info = vehicle_info
                            existing_review.review_text = review_data.get('review_text')
                            existing_review.areas_of_improvement = areas_str
                            existing_review.host_response = review_data.get('host_response')
                            existing_review.has_host_response = review_data.get('has_host_response', False)
                            existing_review.updated_at = datetime.now(timezone.utc)
                            logger.debug(f"Updated existing review: {review_id}")
                        else:
                            # Create new review
                            review = Review(
                                account_id=account_id,
                                turo_review_id=review_id,
                                customer_name=customer_name,
                                customer_id=review_data.get('customer_id'),
                                rating=review_data.get('rating'),
                                date=review_date,
                                vehicle_info=vehicle_info,
                                review_text=review_data.get('review_text'),
                                areas_of_improvement=areas_str,
                                host_response=review_data.get('host_response'),
                                has_host_response=review_data.get('has_host_response', False)
                            )
                            db.add(review)
                            logger.debug(f"Created new review: {review_id}")
                        
                        reviews_saved += 1
                        # Commit after each review to ensure upsert logic works
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.warning(f"Error saving review {review_data.get('customer_id')}: {e}")
                        continue
            
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
            logger.info(f"Found ratings data with {len(scraped_data['ratings'].get('reviews', []))} reviews")
            results['reviews'] = save_reviews_data(account_id, scraped_data['ratings'])
        elif 'reviews' in scraped_data:
            logger.info(f"Found reviews data with {len(scraped_data['reviews'].get('reviews', []))} reviews")
            results['reviews'] = save_reviews_data(account_id, scraped_data['reviews'])
        else:
            logger.warning(f"No ratings/reviews data found in scraped data. Available keys: {list(scraped_data.keys())}")
        
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