import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database.models import (
    Account,
    Vehicle,
    Trip,
    Review,
    EarningsBreakdown,
    VehicleEarnings,
    Transaction,
    Receipt,
)
from core.utils.route_helpers import parse_amount

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ DATABASE SERVICE ------------------------------

class DatabaseService:
    """Service for saving scraped data to the database."""
    
    # ------------------------------ HELPER METHODS ------------------------------
    
    @staticmethod
    def get_account_by_user_id(db: Session, user_id: int) -> Optional[Account]:
        """Get account by user_id (hash-based identifier)."""
        return db.query(Account).filter(Account.user_id == user_id).first()
    
    @staticmethod
    def get_account(db: Session, account_id: int = None, user_id: int = None) -> Optional[Account]:
        """
        Get account by id or user_id. Tries account_id first, then falls back to user_id.
        
        Args:
            db: Database session
            account_id: Account.id to search for
            user_id: Account.user_id to search for (fallback)
        
        Returns:
            Account if found, None otherwise
        """
        if account_id is not None:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                return account
        
        if user_id is not None:
            return DatabaseService.get_account_by_user_id(db, user_id)
        
        return None
    
    @staticmethod
    def get_account_or_raise(db: Session, account_id: int = None, user_id: int = None) -> Account:
        """
        Get account by id or user_id, raise HTTPException if not found.
        
        Args:
            db: Database session
            account_id: Account.id to search for
            user_id: Account.user_id to search for (fallback)
        
        Returns:
            Account if found
        
        Raises:
            HTTPException: If account not found
        """
        from fastapi import HTTPException
        
        account = DatabaseService.get_account(db, account_id=account_id, user_id=user_id)
        if not account:
            identifier = account_id or user_id or "unknown"
            raise HTTPException(status_code=404, detail=f"Account {identifier} not found")
        return account
    
    @staticmethod
    def _get_existing_ids(
        db: Session, 
        user_id: int, 
        model_class, 
        id_column, 
        id_name: str
    ) -> set[str]:
        """Generic method to get existing IDs for an account."""
        account = DatabaseService.get_account_by_user_id(db, user_id)
        if not account:
            return set()
        
        query = db.query(id_column).filter(
            model_class.account_id == account.id,
            id_column.isnot(None)
        ).all()
        existing_ids = {id_value[0] for id_value in query if id_value[0]}
        logger.debug(f"Found {len(existing_ids)} existing {id_name}s for user {user_id}")
        return existing_ids
    
    @staticmethod
    def _truncate_string(value: Optional[str], max_length: int) -> Optional[str]:
        """Truncate string to max_length if it exceeds the limit."""
        if value is None:
            return None
        if len(value) > max_length:
            logger.warning(f"String truncated from {len(value)} to {max_length} characters: {value[:50]}...")
            return value[:max_length]
        return value
    
    @staticmethod
    def _parse_float(value):
        """Parse a value to float, handling None, int, float, and string types."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return parse_amount(value)
        return None
    
    @staticmethod
    def _clean_string_value(value: Optional[str]) -> Optional[str]:
        """Replace '-' with None for string fields."""
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == '-':
            return None
        return value if value else None
    
    @staticmethod
    def _split_vehicle_name_year(vehicle_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Extract year from vehicle name and return cleaned name and year separately."""
        if not vehicle_name:
            return None, None
        
        year_match = re.search(r'(19\d{2}|20\d{2})$', vehicle_name.strip())
        if year_match:
            year = year_match.group(1)
            # Validate year is in reasonable range
            year_int = int(year)
            if 1900 <= year_int <= 2099:
                cleaned_name = vehicle_name[:year_match.start()].strip()
                return cleaned_name, year
        
        return vehicle_name, None
    
    # ------------------------------ PUBLIC METHODS ------------------------------
    
    @staticmethod
    def get_or_create_account(db: Session, user_id: int, email: str) -> Account:
        """
        Get or create an account by user_id and email.
        
        The email parameter is only used when creating a new account.
        This prevents Turo email from overwriting the Turolytics account email.
        """
        account = DatabaseService.get_account_by_user_id(db, user_id)
        if not account:
            account = Account(user_id=user_id, email=email)
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"Created new account: user_id={user_id}, email={email}")
        return account
    
    @staticmethod
    def get_existing_trip_ids(db: Session, user_id: int) -> set[str]:
        """Get set of existing trip_ids for an account to avoid re-scraping."""
        return DatabaseService._get_existing_ids(
            db, user_id, Trip, Trip.trip_id, "trip_id"
        )
    
    @staticmethod
    def get_existing_customer_ids(db: Session, user_id: int) -> set[str]:
        """Get set of existing customer_ids for an account to avoid re-scraping."""
        return DatabaseService._get_existing_ids(
            db, user_id, Review, Review.customer_id, "customer_id"
        )
    
    @staticmethod
    def save_vehicles(db: Session, account: Account, vehicles_data: Dict[str, Any]) -> List[Vehicle]:
        """Save vehicles data."""
        if not vehicles_data or "vehicles" not in vehicles_data:
            return []
        
        vehicles_list = vehicles_data.get("vehicles", [])
        if not vehicles_list:
            return []
        
        license_plates = [v.get("license_plate") for v in vehicles_list if v.get("license_plate")]
        existing_vehicles = {}
        if license_plates:
            existing_vehicles_query = db.query(Vehicle).filter(
                Vehicle.account_id == account.id,
                Vehicle.license_plate.in_(license_plates)
            ).all()
            existing_vehicles = {v.license_plate: v for v in existing_vehicles_query}
        
        saved_vehicles = []
        
        for vehicle_data in vehicles_list:
            license_plate = vehicle_data.get("license_plate")
            vehicle = existing_vehicles.get(license_plate) if license_plate else None
            
            if not vehicle:
                vehicle = Vehicle(account_id=account.id)
                db.add(vehicle)
            
            vehicle.name = DatabaseService._truncate_string(vehicle_data.get("name"), 255) if vehicle_data.get("name") else None
            vehicle.year = vehicle_data.get("year")
            vehicle.trim = vehicle_data.get("trim")
            vehicle.license_plate = license_plate
            vehicle.status = DatabaseService._truncate_string(vehicle_data.get("status"), 255) if vehicle_data.get("status") else None
            vehicle.trip_info = vehicle_data.get("trip_info")
            vehicle.rating = vehicle_data.get("rating")
            vehicle.trip_count = vehicle_data.get("trip_count")
            saved_vehicles.append(vehicle)
        
        try:
            db.commit()
            for vehicle in saved_vehicles:
                db.refresh(vehicle)
            logger.info(f"Saved {len(saved_vehicles)} vehicles for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving vehicles: {e}")
            db.rollback()
            return []
        except Exception as e:
            logger.error(f"Error saving vehicles: {e}")
            db.rollback()
            return []
        
        return saved_vehicles
    
    @staticmethod
    def save_trips(db: Session, account: Account, trips_data: Dict[str, Any]) -> List[Trip]:
        """Save trips data (both booked and history)."""
        saved_trips = []
        
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            """Parse datetime string, handling Z suffix and converting to UTC-aware."""
            if not dt_str:
                return None
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        
        booked_data = trips_data.get("booked_trips", {})
        booked_trips = booked_data.get("trips", [])
        booked_scraped_at = parse_datetime(booked_data.get("scraped_at"))
        
        history_data = trips_data.get("trip_history", {})
        history_trips = history_data.get("trips", [])
        history_scraped_at = parse_datetime(history_data.get("scraped_at"))
        
        all_trips = [
            {**trip_data, "trip_type": "booked_trips", "scraped_at": booked_scraped_at}
            for trip_data in booked_trips
        ] + [
            {**trip_data, "trip_type": "trip_history", "scraped_at": history_scraped_at}
            for trip_data in history_trips
        ]
        
        trip_ids = [t.get("trip_id") for t in all_trips if t.get("trip_id")]
        existing_trips = {}
        if trip_ids:
            existing_trips_query = db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.trip_id.in_(trip_ids)
            ).all()
            existing_trips = {t.trip_id: t for t in existing_trips_query}
        
        license_plates = list({t.get("license_plate") for t in all_trips if t.get("license_plate")})
        vehicles_by_plate = {}
        if license_plates:
            vehicles_query = db.query(Vehicle).filter(
                Vehicle.account_id == account.id,
                Vehicle.license_plate.in_(license_plates)
            ).all()
            vehicles_by_plate = {v.license_plate: v for v in vehicles_query}
        
        for trip_data in all_trips:
            trip_id_str = trip_data.get("trip_id")
            if not trip_id_str:
                continue
            
            trip = existing_trips.get(trip_id_str)
            
            if not trip:
                trip = Trip(account_id=account.id)
                db.add(trip)
            
            license_plate = trip_data.get("license_plate")
            if license_plate:
                vehicle = vehicles_by_plate.get(license_plate)
                if vehicle:
                    trip.vehicle_id = vehicle.id
            
            trip.trip_id = DatabaseService._truncate_string(trip_id_str, 100)
            trip.customer_name = trip_data.get("customer_name")
            trip.status = DatabaseService._truncate_string(trip_data.get("status"), 255) if trip_data.get("status") else None
            trip.trip_type = trip_data.get("trip_type")
            trip.cancellation_info = DatabaseService._truncate_string(trip_data.get("cancellation_info"), 255)
            trip.cancelled_by = trip_data.get("cancelled_by")
            trip.cancelled_date = trip_data.get("cancelled_date")
            
            schedule_data = trip_data.get("schedule", {})
            trip.start_date = schedule_data.get("start_date")
            trip.start_time = schedule_data.get("start_time")
            trip.end_date = schedule_data.get("end_date")
            trip.end_time = schedule_data.get("end_time")
            
            location_data = trip_data.get("location", {})
            trip.location_type = location_data.get("location_type")
            trip.location = DatabaseService._truncate_string(location_data.get("address"), 255)
            
            kilometers_data = trip_data.get("kilometers", {})
            trip.kilometers_included = kilometers_data.get("kilometers_included")
            trip.kilometers_driven = kilometers_data.get("kilometers_driven")
            trip.overage_rate = kilometers_data.get("overage_rate")
            
            earnings_data = trip_data.get("earnings", {})
            trip.total_earnings = earnings_data.get("total_earnings")
            
            protection_data = trip_data.get("protection", {})
            trip.protection_plan = protection_data.get("protection_plan")
            trip.deductible = protection_data.get("deductible")
            
            saved_trips.append(trip)
        
        try:
            db.commit()
            for trip in saved_trips:
                db.refresh(trip)
            logger.info(f"Saved {len(saved_trips)} trips for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving trips: {e}")
            db.rollback()
            return []
        except Exception as e:
            logger.error(f"Error saving trips: {e}")
            db.rollback()
            return []
        
        return saved_trips
    
    
    @staticmethod
    def save_receipts(db: Session, account: Account, receipts_data: Dict[str, Any]) -> int:
        """Save receipt data for trips.
        
        Args:
            db: Database session
            account: Account object
            receipts_data: Dictionary with 'receipts' key containing dict of trip_id -> receipt_data or list of receipt data dicts
        
        Returns:
            Number of receipts saved
        """
        if not receipts_data or "receipts" not in receipts_data:
            return 0
        
        receipts_raw = receipts_data.get("receipts", {})
        
        if isinstance(receipts_raw, dict):
            receipts_list = [dict(receipt_data, reservation_id=trip_id) for trip_id, receipt_data in receipts_raw.items()]
        else:
            receipts_list = receipts_raw
        
        if not receipts_list:
            return 0
        
        reservation_ids = [r.get("reservation_id") for r in receipts_list if r.get("reservation_id")]
        existing_receipts = {}
        if reservation_ids:
            existing_receipts_query = db.query(Receipt).filter(
                Receipt.account_id == account.id,
                Receipt.reservation_id.in_(reservation_ids)
            ).all()
            existing_receipts = {r.reservation_id: r for r in existing_receipts_query}
        
        saved_receipts = []
        
        for receipt_data in receipts_list:
            if not receipt_data:
                continue
            
            reservation_id = receipt_data.get("reservation_id")
            if not reservation_id:
                logger.warning("Receipt data missing reservation_id, skipping.")
                continue
            
            receipt = existing_receipts.get(reservation_id)
            
            # Extract trip_price and delivery_fee from receipt_data
            trip_price = DatabaseService._parse_float(receipt_data.get("trip_price"))
            delivery_fee = DatabaseService._parse_float(receipt_data.get("delivery_fee"))
            turo_fees = DatabaseService._parse_float(receipt_data.get("turo_fees"))
            sales_tax = DatabaseService._parse_float(receipt_data.get("sales_tax"))
            
            # Clean vehicle_name
            vehicle_name_raw = receipt_data.get("vehicle_name")
            vehicle_name_cleaned, extracted_year = DatabaseService._split_vehicle_name_year(vehicle_name_raw)
            # Use extracted year if vehicle_year not already set
            vehicle_year = receipt_data.get("vehicle_year") or extracted_year
            
            # Clean string values (replace '-' with None)
            booked_date_clean = DatabaseService._clean_string_value(receipt_data.get("booked_date") or receipt_data.get("booked_at"))
            trip_start_clean = DatabaseService._clean_string_value(receipt_data.get("trip_start") or receipt_data.get("trip_start_date"))
            trip_end_clean = DatabaseService._clean_string_value(receipt_data.get("trip_end") or receipt_data.get("trip_end_date"))
            pickup_location_clean = DatabaseService._clean_string_value(receipt_data.get("pickup_location"))
            return_location_clean = DatabaseService._clean_string_value(receipt_data.get("return_location"))
            guest_name_clean = DatabaseService._clean_string_value(receipt_data.get("guest_name"))
            
            if not receipt:
                # Create new receipt
                receipt = Receipt(
                    account_id=account.id,
                    reservation_id=reservation_id,
                    vehicle_name=DatabaseService._truncate_string(vehicle_name_cleaned, 255),
                    vehicle_year=vehicle_year,
                    booked_date=booked_date_clean,
                    trip_start=trip_start_clean,
                    trip_end=trip_end_clean,
                    pickup_location=DatabaseService._truncate_string(pickup_location_clean, 255),
                    return_location=DatabaseService._truncate_string(return_location_clean, 255),
                    guest_name=DatabaseService._truncate_string(guest_name_clean, 255),
                    distance_included=receipt_data.get("distance_included"),
                    overage_rate=DatabaseService._parse_float(receipt_data.get("overage_rate") or receipt_data.get("overage_fee_per_km")),
                    trip_price=trip_price,
                    delivery_fee=delivery_fee,
                    trip_total=DatabaseService._parse_float(receipt_data.get("trip_total")),
                    turo_fees=DatabaseService._parse_float(receipt_data.get("turo_fees")) or turo_fees,
                    sales_tax=DatabaseService._parse_float(receipt_data.get("sales_tax")) or sales_tax,
                    you_earned=DatabaseService._parse_float(receipt_data.get("you_earned"))
                )
                db.add(receipt)  # Add to session before saving
            else:
                # Update existing receipt
                receipt.vehicle_name = DatabaseService._truncate_string(vehicle_name_cleaned, 255) or receipt.vehicle_name
                receipt.vehicle_year = vehicle_year or receipt.vehicle_year
                receipt.booked_date = booked_date_clean or receipt.booked_date
                receipt.trip_start = trip_start_clean or receipt.trip_start
                receipt.trip_end = trip_end_clean or receipt.trip_end
                receipt.pickup_location = DatabaseService._truncate_string(pickup_location_clean, 255) or receipt.pickup_location
                receipt.return_location = DatabaseService._truncate_string(return_location_clean, 255) or receipt.return_location
                receipt.guest_name = DatabaseService._truncate_string(guest_name_clean, 255) or receipt.guest_name
                receipt.distance_included = receipt_data.get("distance_included") or receipt.distance_included
                receipt.overage_rate = DatabaseService._parse_float(receipt_data.get("overage_rate") or receipt_data.get("overage_fee_per_km")) or receipt.overage_rate
                receipt.trip_price = trip_price or receipt.trip_price
                receipt.delivery_fee = delivery_fee or receipt.delivery_fee
                receipt.trip_total = DatabaseService._parse_float(receipt_data.get("trip_total")) or receipt.trip_total
                receipt.turo_fees = turo_fees or receipt.turo_fees
                receipt.sales_tax = sales_tax or receipt.sales_tax
                receipt.you_earned = DatabaseService._parse_float(receipt_data.get("you_earned")) or receipt.you_earned
            
            saved_receipts.append(receipt)
        
        try:
            db.commit()
            for receipt in saved_receipts:
                db.refresh(receipt)
            logger.info(f"Saved {len(saved_receipts)} receipts for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving receipts: {e}")
            db.rollback()
            return 0
        except Exception as e:
            logger.error(f"Error saving receipts: {e}")
            db.rollback()
            return 0
        
        return len(saved_receipts)
    
    @staticmethod
    def _clean_host_response(response_text: Optional[str]) -> Optional[str]:
        """Remove 'Your response' prefix from host response text (case-insensitive)."""
        if not response_text:
            return None
        
        cleaned = re.sub(r'^Your\s+response\s*', '', response_text, flags=re.IGNORECASE)
        return cleaned.strip() if cleaned.strip() else None
    
    @staticmethod
    def save_reviews(db: Session, account: Account, reviews_data: Dict[str, Any]) -> List[Review]:
        """Save reviews data."""
        if not reviews_data or "reviews" not in reviews_data:
            return []
        
        reviews_list = reviews_data.get("reviews", [])
        if not reviews_list:
            return []
        
        customer_ids = [r.get("customer_id") for r in reviews_list if r.get("customer_id")]
        existing_reviews = {}
        if customer_ids:
            existing_reviews_query = db.query(Review).filter(
                Review.account_id == account.id,
                Review.customer_id.in_(customer_ids)
            ).all()
            existing_reviews = {r.customer_id: r for r in existing_reviews_query}
        
        license_plates = []
        for review_data in reviews_list:
            vehicle_info = review_data.get("vehicle_info")
            if vehicle_info:
                plate_match = re.search(r'•\s*([A-Z0-9-]+)', vehicle_info)
                if plate_match:
                    license_plates.append(plate_match.group(1))
                else:
                    parts = vehicle_info.split()
                    if len(parts) > 0:
                        potential_plate = parts[-1]
                        if re.match(r'^[A-Z0-9-]{4,}$', potential_plate):
                            license_plates.append(potential_plate)
        
        vehicles_by_plate = {}
        if license_plates:
            vehicles_query = db.query(Vehicle).filter(
                Vehicle.account_id == account.id,
                Vehicle.license_plate.in_(license_plates)
            ).all()
            vehicles_by_plate = {v.license_plate: v for v in vehicles_query}
        
        saved_reviews = []
        
        for review_data in reviews_list:
            customer_id = review_data.get("customer_id")
            
            review = existing_reviews.get(customer_id) if customer_id else None
            
            if not review:
                review = Review(account_id=account.id)
                db.add(review)
            
            review.customer_name = review_data.get("customer_name")
            review.customer_id = customer_id
            review.rating = review_data.get("rating")
            review.vehicle_info = review_data.get("vehicle_info")
            review.review_text = review_data.get("review_text")
            review.areas_of_improvement = review_data.get("areas_of_improvement", [])
            raw_response = review_data.get("host_response")
            review.host_response = DatabaseService._clean_host_response(raw_response)
            review.has_host_response = bool(review.host_response)
            
            vehicle_info = review_data.get("vehicle_info")
            if vehicle_info:
                license_plate = None
                plate_match = re.search(r'•\s*([A-Z0-9-]+)', vehicle_info)
                if plate_match:
                    license_plate = plate_match.group(1)
                else:
                    parts = vehicle_info.split()
                    if len(parts) > 0:
                        potential_plate = parts[-1]
                        if re.match(r'^[A-Z0-9-]{4,}$', potential_plate):
                            license_plate = potential_plate
                
                if license_plate:
                    vehicle = vehicles_by_plate.get(license_plate)
                    if vehicle:
                        review.vehicle_id = vehicle.id
                        logger.debug(f"Linked review to vehicle {vehicle.id} via license plate {license_plate}")
            
            date_str = review_data.get("date")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    review.date = dt
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse review date: {date_str}")
            
            saved_reviews.append(review)
        
        try:
            db.commit()
            for review in saved_reviews:
                db.refresh(review)
            logger.info(f"Saved {len(saved_reviews)} reviews for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving reviews: {e}")
            db.rollback()
            return []
        except Exception as e:
            logger.error(f"Error saving reviews: {e}")
            db.rollback()
            return []
        
        return saved_reviews
    
    @staticmethod
    def save_earnings(db: Session, account: Account, earnings_data: Dict[str, Any]) -> tuple[List[EarningsBreakdown], List[VehicleEarnings]]:
        """Save earnings data."""
        saved_breakdowns = []
        saved_vehicle_earnings = []
        
        if earnings_data.get("earnings_breakdown"):
            breakdowns_list = earnings_data["earnings_breakdown"]
            breakdown_keys = [(b.get("type"), b.get("year")) for b in breakdowns_list if b.get("type") and b.get("year")]
            existing_breakdowns = {}
            if breakdown_keys:
                # Query only the breakdowns we need, not all for the account
                existing_breakdowns_query = db.query(EarningsBreakdown).filter(
                    EarningsBreakdown.account_id == account.id,
                    EarningsBreakdown.type.in_([k[0] for k in breakdown_keys]),
                    EarningsBreakdown.year.in_([k[1] for k in breakdown_keys])
                ).all()
                existing_breakdowns = {(b.type, b.year): b for b in existing_breakdowns_query if (b.type, b.year) in breakdown_keys}
            
            for breakdown_data in breakdowns_list:
                breakdown_key = (breakdown_data.get("type"), breakdown_data.get("year"))
                breakdown = existing_breakdowns.get(breakdown_key) if breakdown_key[0] and breakdown_key[1] else None
                
                if not breakdown:
                    breakdown = EarningsBreakdown(
                        account_id=account.id,
                        type=breakdown_data.get("type"),
                        amount=breakdown_data.get("amount"),
                        amount_numeric=parse_amount(breakdown_data.get("amount")),
                        year=breakdown_data.get("year")
                    )
                    db.add(breakdown)
                else:
                    breakdown.amount = breakdown_data.get("amount")
                    breakdown.amount_numeric = parse_amount(breakdown_data.get("amount"))
                
                saved_breakdowns.append(breakdown)
        
        if earnings_data.get("vehicle_earnings"):
            vehicle_earnings_list = earnings_data["vehicle_earnings"]
            vehicle_earnings_keys = []
            for ve_data in vehicle_earnings_list:
                if ve_data.get("license_plate") and ve_data.get("year"):
                    vehicle_earnings_keys.append(("plate", ve_data.get("license_plate"), ve_data.get("year")))
                elif ve_data.get("vehicle_name") and ve_data.get("trim") and ve_data.get("year"):
                    vehicle_earnings_keys.append(("name", ve_data.get("vehicle_name"), ve_data.get("trim"), ve_data.get("year")))
            
            existing_vehicle_earnings = {}
            if vehicle_earnings_list:
                existing_ve_query = db.query(VehicleEarnings).filter(
                    VehicleEarnings.account_id == account.id
                ).all()
                for ve in existing_ve_query:
                    if ve.license_plate and ve.year:
                        existing_vehicle_earnings[("plate", ve.license_plate, ve.year)] = ve
                    if ve.vehicle_name and ve.trim and ve.year:
                        existing_vehicle_earnings[("name", ve.vehicle_name, ve.trim, ve.year)] = ve
            
            for vehicle_earnings_data in vehicle_earnings_list:
                year = vehicle_earnings_data.get("year")
                vehicle_earnings = None
                
                if vehicle_earnings_data.get("license_plate") and year:
                    vehicle_earnings = existing_vehicle_earnings.get(("plate", vehicle_earnings_data.get("license_plate"), year))
                
                if not vehicle_earnings and vehicle_earnings_data.get("vehicle_name") and vehicle_earnings_data.get("trim") and year:
                    vehicle_earnings = existing_vehicle_earnings.get(("name", vehicle_earnings_data.get("vehicle_name"), vehicle_earnings_data.get("trim"), year))
                
                if not vehicle_earnings:
                    vehicle_earnings = VehicleEarnings(
                        account_id=account.id,
                        vehicle_name=vehicle_earnings_data.get("vehicle_name"),
                        license_plate=vehicle_earnings_data.get("license_plate"),
                        trim=vehicle_earnings_data.get("trim"),
                        earnings_amount=vehicle_earnings_data.get("earnings_amount"),
                        earnings_amount_numeric=parse_amount(vehicle_earnings_data.get("earnings_amount")),
                        year=year
                    )
                    db.add(vehicle_earnings)
                else:
                    vehicle_earnings.vehicle_name = vehicle_earnings_data.get("vehicle_name")
                    vehicle_earnings.license_plate = vehicle_earnings_data.get("license_plate")
                    vehicle_earnings.trim = vehicle_earnings_data.get("trim")
                    vehicle_earnings.earnings_amount = vehicle_earnings_data.get("earnings_amount")
                    vehicle_earnings.earnings_amount_numeric = parse_amount(vehicle_earnings_data.get("earnings_amount"))
                    vehicle_earnings.year = year
                
                saved_vehicle_earnings.append(vehicle_earnings)
        
        try:
            db.commit()
            for breakdown in saved_breakdowns:
                db.refresh(breakdown)
            for vehicle_earnings in saved_vehicle_earnings:
                db.refresh(vehicle_earnings)
            logger.info(f"Saved {len(saved_breakdowns)} earnings breakdowns and {len(saved_vehicle_earnings)} vehicle earnings for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving earnings: {e}")
            db.rollback()
            return [], []
        except Exception as e:
            logger.error(f"Error saving earnings: {e}")
            db.rollback()
            return [], []
        
        return saved_breakdowns, saved_vehicle_earnings
    
    @staticmethod
    def has_existing_earnings(db: Session, user_id: int) -> bool:
        """Check if account has existing earnings data."""
        account = DatabaseService.get_account_by_user_id(db, user_id)
        if not account:
            return False
        
        has_breakdown = db.query(EarningsBreakdown).filter(
            EarningsBreakdown.account_id == account.id
        ).first() is not None
        
        has_vehicle_earnings = db.query(VehicleEarnings).filter(
            VehicleEarnings.account_id == account.id
        ).first() is not None
        
        return has_breakdown or has_vehicle_earnings
    
    @staticmethod
    def has_existing_transactions(db: Session, user_id: int) -> bool:
        """Check if account has existing transactions data."""
        account = DatabaseService.get_account_by_user_id(db, user_id)
        if not account:
            return False
        
        return db.query(Transaction).filter(
            Transaction.account_id == account.id
        ).first() is not None
    
    @staticmethod
    def save_transactions(db: Session, account: Account, transactions_data: Dict[str, Any]) -> List[Transaction]:
        """Save transactions data."""
        saved_transactions = []
        
        if not transactions_data or "transactions" not in transactions_data:
            return saved_transactions
        
        transactions_list = transactions_data.get("transactions", [])
        
        if not transactions_list:
            return saved_transactions
        
        logger.info(f"Attempting to save {len(transactions_list)} transactions for account {account.user_id}")
        
        reservation_ids = [t.get("reservation_id") for t in transactions_list if t.get("reservation_id")]
        trips_by_reservation = {}
        if reservation_ids:
            trips_query = db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.trip_id.in_(reservation_ids)
            ).all()
            trips_by_reservation = {t.trip_id: t for t in trips_query}
        
        vehicle_names = list({t.get("vehicle_name") for t in transactions_list if t.get("vehicle_name")})
        vehicles_by_name = {}
        if vehicle_names:
            vehicles_query = db.query(Vehicle).filter(
                Vehicle.account_id == account.id,
                Vehicle.name.in_(vehicle_names)
            ).all()
            vehicles_by_name = {v.name: v for v in vehicles_query}
        
        transaction_keys = []
        for t in transactions_list:
            reservation_id = t.get("reservation_id")
            date = t.get("date")
            transaction_type = t.get("type")
            year = t.get("year")
            if reservation_id and date and transaction_type and year:
                transaction_keys.append(("reservation", reservation_id, date, transaction_type, year))
            elif date and transaction_type and year:
                payment_details = t.get("payment_details")
                transaction_keys.append(("payment", date, transaction_type, year, payment_details))
        
        existing_transactions = {}
        if transaction_keys:
            # Extract unique dates, types, and years to query only what we need
            dates = list({k[1] if k[0] == "reservation" else k[1] for k in transaction_keys})
            types = list({k[2] if k[0] == "reservation" else k[2] for k in transaction_keys})
            years = list({k[3] if k[0] == "reservation" else k[3] for k in transaction_keys})
            reservation_ids = list({k[1] for k in transaction_keys if k[0] == "reservation"})
            
            # Query only transactions matching our keys (much more efficient than loading all)
            query = db.query(Transaction).filter(
                Transaction.account_id == account.id,
                Transaction.date.in_(dates),
                Transaction.type.in_(types),
                Transaction.year.in_(years)
            )
            # If we have reservation-based keys, also filter by reservation_id
            if reservation_ids:
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Transaction.reservation_id.in_(reservation_ids),
                        Transaction.reservation_id.is_(None)
                    )
                )
            
            all_existing = query.all()
            for trans in all_existing:
                if trans.reservation_id and trans.date and trans.type and trans.year:
                    key = ("reservation", trans.reservation_id, trans.date, trans.type, trans.year)
                    if key in transaction_keys:
                        existing_transactions[key] = trans
                elif trans.date and trans.type and trans.year and trans.payment_details:
                    key = ("payment", trans.date, trans.type, trans.year, trans.payment_details)
                    if key in transaction_keys:
                        existing_transactions[key] = trans
        
        for idx, transaction_data in enumerate(transactions_list, 1):
            logger.debug(f"Processing transaction {idx}/{len(transactions_list)}: {transaction_data.get('type')} | {transaction_data.get('date')} | {transaction_data.get('reservation_id') or 'N/A'}")
            reservation_id = transaction_data.get("reservation_id")
            date = transaction_data.get("date")
            transaction_type = transaction_data.get("type")
            year = transaction_data.get("year")
            
            vehicle_id = None
            
            if reservation_id:
                trip = trips_by_reservation.get(reservation_id)
                if trip:
                    vehicle_id = trip.vehicle_id
            
            if not vehicle_id and transaction_data.get("vehicle_name"):
                vehicle = vehicles_by_name.get(transaction_data.get("vehicle_name"))
                if vehicle:
                    vehicle_id = vehicle.id
            
            existing_transaction = None
            if reservation_id and date and transaction_type and year:
                key = ("reservation", reservation_id, date, transaction_type, year)
                existing_transaction = existing_transactions.get(key)
            elif date and transaction_type and year:
                key = ("payment", date, transaction_type, year, transaction_data.get("payment_details"))
                existing_transaction = existing_transactions.get(key)
            
            if not existing_transaction:
                existing_transaction = Transaction(
                    account_id=account.id,
                    vehicle_id=vehicle_id,
                    type=transaction_type,
                    trip_name=transaction_data.get("trip_name"),
                    vehicle_name=transaction_data.get("vehicle_name"),
                    payment_details=transaction_data.get("payment_details"),
                    reservation_id=reservation_id,
                    date=date,
                    year=year,
                    earnings_amount=transaction_data.get("earnings_amount"),
                    earnings_amount_numeric=transaction_data.get("earnings_amount_numeric"),
                    payment_amount=transaction_data.get("payment_amount"),
                    payment_amount_numeric=transaction_data.get("payment_amount_numeric")
                )
                db.add(existing_transaction)
                logger.info(f"  [{idx}] NEW transaction: {transaction_type} | {transaction_data.get('trip_name') or transaction_data.get('payment_details')} | {date} | {reservation_id or 'N/A'}")
            else:
                existing_transaction.vehicle_id = vehicle_id or existing_transaction.vehicle_id
                existing_transaction.trip_name = transaction_data.get("trip_name") or existing_transaction.trip_name
                existing_transaction.vehicle_name = transaction_data.get("vehicle_name") or existing_transaction.vehicle_name
                existing_transaction.payment_details = transaction_data.get("payment_details") or existing_transaction.payment_details
                existing_transaction.earnings_amount = transaction_data.get("earnings_amount") or existing_transaction.earnings_amount
                existing_transaction.earnings_amount_numeric = transaction_data.get("earnings_amount_numeric") or existing_transaction.earnings_amount_numeric
                existing_transaction.payment_amount = transaction_data.get("payment_amount") or existing_transaction.payment_amount
                existing_transaction.payment_amount_numeric = transaction_data.get("payment_amount_numeric") or existing_transaction.payment_amount_numeric
                logger.info(f"  [{idx}] UPDATED existing transaction: {transaction_type} | {date} | {reservation_id or 'N/A'}")
            
            saved_transactions.append(existing_transaction)
        
        try:
            db.commit()
            for transaction in saved_transactions:
                db.refresh(transaction)
            logger.info(f"Saved {len(saved_transactions)} transactions for account {account.user_id}")
        except IntegrityError as e:
            logger.error(f"Integrity error saving transactions: {e}")
            db.rollback()
            return []
        except Exception as e:
            logger.error(f"Error saving transactions: {e}")
            db.rollback()
            return []
        
        return saved_transactions
    
    @staticmethod
    def save_scraped_data(db: Session, user_id: int, email: str, scraped_data: Dict[str, Any]) -> bool:
        """
        Save all scraped data to database.
        
        Note: This method uses a best-effort per-section approach. Each section
        (vehicles, trips, reviews, earnings, transactions, receipts) commits
        independently. If one section fails, earlier sections are already committed
        and will remain in the database. This is intentional to maximize data
        preservation even if one section has issues.
        
        For true all-or-nothing behavior, wrap this in a transaction boundary
        and modify individual save_* methods to use flush() instead of commit().
        """
        try:
            account = DatabaseService.get_or_create_account(db, user_id, email)
            
            if "vehicles" in scraped_data:
                DatabaseService.save_vehicles(db, account, scraped_data["vehicles"])
            
            if "trips" in scraped_data:
                DatabaseService.save_trips(db, account, scraped_data["trips"])
            
            if "reviews" in scraped_data:
                DatabaseService.save_reviews(db, account, scraped_data["reviews"])
            
            if "earnings" in scraped_data:
                DatabaseService.save_earnings(db, account, scraped_data["earnings"])
            
            if "transactions" in scraped_data:
                DatabaseService.save_transactions(db, account, scraped_data["transactions"])
            
            if "receipts" in scraped_data:
                DatabaseService.save_receipts(db, account, scraped_data["receipts"])
            
            logger.info(f"Successfully saved all scraped data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scraped data to database: {e}")
            db.rollback()
            return False

# ------------------------------ END OF FILE ------------------------------
