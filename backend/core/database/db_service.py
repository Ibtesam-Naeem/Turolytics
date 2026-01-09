import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

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
        if account_id:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                return account
        
        if user_id:
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
    def _save_entity(
        db: Session,
        entity,
        error_context: str = "entity"
    ) -> bool:
        """Generic method to save a single entity with error handling."""
        try:
            db.commit()
            db.refresh(entity)
            return True
        except Exception as e:
            logger.error(f"Error saving {error_context}: {e}")
            db.rollback()
            return False
    
    # ------------------------------ PUBLIC METHODS ------------------------------
    
    @staticmethod
    def get_or_create_account(db: Session, user_id: int, email: str) -> Account:
        """
        Get or create an account by user_id and email.
        
        Note: If account already exists, we do NOT update the email.
        The email parameter is only used when creating a new account.
        This prevents Turo email from overwriting the Turolytics account email.
        The Turo email should be stored in TuroIntegration.turo_email, not Account.email.
        """
        account = DatabaseService.get_account_by_user_id(db, user_id)
        if not account:
            account = Account(user_id=user_id, email=email)
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"Created new account: user_id={user_id}, email={email}")
        # Do NOT update email if account exists - preserve the original Turolytics account email
        # The email parameter here might be a Turo email, which should be stored in TuroIntegration, not Account
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
        
        saved_vehicles = []
        
        for vehicle_data in vehicles_data.get("vehicles", []):
            vehicle = None
            if vehicle_data.get("license_plate"):
                vehicle = db.query(Vehicle).filter(
                    Vehicle.account_id == account.id,
                    Vehicle.license_plate == vehicle_data["license_plate"]
                ).first()
            
            if not vehicle:
                vehicle = Vehicle(account_id=account.id)
                db.add(vehicle)
            
            vehicle.name = vehicle_data.get("name")
            vehicle.year = vehicle_data.get("year")
            vehicle.trim = vehicle_data.get("trim")
            vehicle.license_plate = vehicle_data.get("license_plate")
            vehicle.status = vehicle_data.get("status")
            vehicle.trip_info = vehicle_data.get("trip_info")
            vehicle.rating = vehicle_data.get("rating")
            vehicle.trip_count = vehicle_data.get("trip_count")
            
            if DatabaseService._save_entity(db, vehicle, f"vehicle {vehicle_data.get('license_plate', 'unknown')}"):
                saved_vehicles.append(vehicle)
        
        logger.info(f"Saved {len(saved_vehicles)} vehicles for account {account.user_id}")
        return saved_vehicles
    
    @staticmethod
    def save_trips(db: Session, account: Account, trips_data: Dict[str, Any]) -> List[Trip]:
        """Save trips data (both booked and history)."""
        saved_trips = []
        
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            """Parse datetime string, handling Z suffix."""
            if not dt_str:
                return None
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        
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
        
        for trip_data in all_trips:
            trip_id_str = trip_data.get("trip_id")
            if not trip_id_str:
                continue
            
            trip = db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.trip_id == trip_id_str
            ).first()
            
            if not trip:
                trip = Trip(account_id=account.id)
                db.add(trip)
            
            if trip_data.get("license_plate"):
                vehicle = db.query(Vehicle).filter(
                    Vehicle.account_id == account.id,
                    Vehicle.license_plate == trip_data["license_plate"]
                ).first()
                if vehicle:
                    trip.vehicle_id = vehicle.id
            
            trip.trip_id = trip_id_str
            trip.customer_name = trip_data.get("customer_name")
            trip.status = trip_data.get("status")
            trip.trip_type = trip_data.get("trip_type")
            trip.cancellation_info = trip_data.get("cancellation_info")
            trip.cancelled_by = trip_data.get("cancelled_by")
            trip.cancelled_date = trip_data.get("cancelled_date")
            
            schedule_data = trip_data.get("schedule", {})
            trip.start_date = schedule_data.get("start_date")
            trip.start_time = schedule_data.get("start_time")
            trip.end_date = schedule_data.get("end_date")
            trip.end_time = schedule_data.get("end_time")
            
            location_data = trip_data.get("location", {})
            trip.location_type = location_data.get("location_type")
            trip.location = location_data.get("address")
            
            kilometers_data = trip_data.get("kilometers", {})
            trip.kilometers_included = kilometers_data.get("kilometers_included")
            trip.kilometers_driven = kilometers_data.get("kilometers_driven")
            trip.overage_rate = kilometers_data.get("overage_rate")
            
            earnings_data = trip_data.get("earnings", {})
            trip.total_earnings = earnings_data.get("total_earnings")
            
            protection_data = trip_data.get("protection", {})
            trip.protection_plan = protection_data.get("protection_plan")
            trip.deductible = protection_data.get("deductible")
            
            # Save receipt data if present
            
            if DatabaseService._save_entity(db, trip, f"trip {trip_id_str}"):
                saved_trips.append(trip)
        
        logger.info(f"Saved {len(saved_trips)} trips for account {account.user_id}")
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
        
        # Handle both dict (trip_id -> receipt_data) and list formats
        if isinstance(receipts_raw, dict):
            receipts_list = [dict(receipt_data, reservation_id=trip_id) for trip_id, receipt_data in receipts_raw.items()]
        else:
            receipts_list = receipts_raw
        saved_count = 0
        
        for receipt_data in receipts_list:
            if not receipt_data:
                continue
            
            reservation_id = receipt_data.get("reservation_id")
            if not reservation_id:
                logger.warning("Receipt data missing reservation_id, skipping.")
                continue
            
            # Check if receipt already exists (by reservation_id)
            receipt = db.query(Receipt).filter(
                Receipt.account_id == account.id,
                Receipt.reservation_id == reservation_id
            ).first()
            
            # Parse amounts from strings to floats
            def parse_float(value):
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    return parse_amount(value)
                return None
            
            # Helper to replace '-' with None
            def clean_string_value(value: Optional[str]) -> Optional[str]:
                """Replace '-' with None for string fields."""
                if value is None:
                    return None
                if isinstance(value, str) and value.strip() == '-':
                    return None
                return value if value else None
            
            # Clean vehicle_name - remove year if present (e.g., "Hyundai Elantra2017" -> "Hyundai Elantra")
            def clean_vehicle_name(vehicle_name: Optional[str]) -> tuple[Optional[str], Optional[str]]:
                """Extract year from vehicle name and return cleaned name and year separately."""
                if not vehicle_name:
                    return None, None
                
                import re
                # Look for 4-digit year at the end, but only valid years (1900-2099)
                # This prevents matching invalid years like "7020" from "Genesis G70"
                year_match = re.search(r'(19\d{2}|20\d{2})$', vehicle_name.strip())
                if year_match:
                    year = year_match.group(1)
                    # Validate year is in reasonable range
                    year_int = int(year)
                    if 1900 <= year_int <= 2099:
                        cleaned_name = vehicle_name[:year_match.start()].strip()
                        return cleaned_name, year
                
                return vehicle_name, None
            
            # Extract trip_price and delivery_fee from receipt_data
            trip_price = parse_float(receipt_data.get("trip_price"))
            delivery_fee = parse_float(receipt_data.get("delivery_fee"))
            turo_fees = parse_float(receipt_data.get("turo_fees"))
            sales_tax = parse_float(receipt_data.get("sales_tax"))
            
            # Clean vehicle_name
            vehicle_name_raw = receipt_data.get("vehicle_name")
            vehicle_name_cleaned, extracted_year = clean_vehicle_name(vehicle_name_raw)
            # Use extracted year if vehicle_year not already set
            vehicle_year = receipt_data.get("vehicle_year") or extracted_year
            
            # Clean string values (replace '-' with None)
            booked_date_clean = clean_string_value(receipt_data.get("booked_date") or receipt_data.get("booked_at"))
            trip_start_clean = clean_string_value(receipt_data.get("trip_start") or receipt_data.get("trip_start_date"))
            trip_end_clean = clean_string_value(receipt_data.get("trip_end") or receipt_data.get("trip_end_date"))
            pickup_location_clean = clean_string_value(receipt_data.get("pickup_location"))
            return_location_clean = clean_string_value(receipt_data.get("return_location"))
            guest_name_clean = clean_string_value(receipt_data.get("guest_name"))
            
            if not receipt:
                # Create new receipt
                receipt = Receipt(
                    account_id=account.id,
                    reservation_id=reservation_id,
                    vehicle_name=vehicle_name_cleaned,
                    vehicle_year=vehicle_year,
                    booked_date=booked_date_clean,
                    trip_start=trip_start_clean,
                    trip_end=trip_end_clean,
                    pickup_location=pickup_location_clean,
                    return_location=return_location_clean,
                    guest_name=guest_name_clean,
                    distance_included=receipt_data.get("distance_included"),
                    overage_rate=parse_float(receipt_data.get("overage_rate") or receipt_data.get("overage_fee_per_km")),
                    trip_price=trip_price,
                    delivery_fee=delivery_fee,
                    trip_total=parse_float(receipt_data.get("trip_total")),
                    turo_fees=parse_float(receipt_data.get("turo_fees")) or turo_fees,
                    sales_tax=parse_float(receipt_data.get("sales_tax")) or sales_tax,
                    you_earned=parse_float(receipt_data.get("you_earned"))
                )
                db.add(receipt)  # Add to session before saving
            else:
                # Update existing receipt
                receipt.vehicle_name = vehicle_name_cleaned or receipt.vehicle_name
                receipt.vehicle_year = vehicle_year or receipt.vehicle_year
                receipt.booked_date = booked_date_clean or receipt.booked_date
                receipt.trip_start = trip_start_clean or receipt.trip_start
                receipt.trip_end = trip_end_clean or receipt.trip_end
                receipt.pickup_location = pickup_location_clean or receipt.pickup_location
                receipt.return_location = return_location_clean or receipt.return_location
                receipt.guest_name = guest_name_clean or receipt.guest_name
                receipt.distance_included = receipt_data.get("distance_included") or receipt.distance_included
                receipt.overage_rate = parse_float(receipt_data.get("overage_rate") or receipt_data.get("overage_fee_per_km")) or receipt.overage_rate
                receipt.trip_price = trip_price or receipt.trip_price
                receipt.delivery_fee = delivery_fee or receipt.delivery_fee
                receipt.trip_total = parse_float(receipt_data.get("trip_total")) or receipt.trip_total
                receipt.turo_fees = turo_fees or receipt.turo_fees
                receipt.sales_tax = sales_tax or receipt.sales_tax
                receipt.you_earned = parse_float(receipt_data.get("you_earned")) or receipt.you_earned
            
            if DatabaseService._save_entity(db, receipt, f"receipt for trip {reservation_id}"):
                saved_count += 1
                logger.debug(f"Saved receipt data for trip {reservation_id}")
        
        logger.info(f"Saved {saved_count} receipts for account {account.user_id}")
        return saved_count
    
    @staticmethod
    def _clean_host_response(response_text: Optional[str]) -> Optional[str]:
        """Remove 'Your response' prefix from host response text (case-insensitive)."""
        if not response_text:
            return None
        
        # Remove 'Your response' or 'Your Response' from the beginning (case-insensitive)
        cleaned = re.sub(r'^Your\s+response\s*', '', response_text, flags=re.IGNORECASE)
        return cleaned.strip() if cleaned.strip() else None
    
    @staticmethod
    def save_reviews(db: Session, account: Account, reviews_data: Dict[str, Any]) -> List[Review]:
        """Save reviews data."""
        if not reviews_data or "reviews" not in reviews_data:
            return []
        
        saved_reviews = []
        
        for review_data in reviews_data.get("reviews", []):
            customer_id = review_data.get("customer_id")
            
            review = None
            if customer_id:
                review = db.query(Review).filter(
                    Review.account_id == account.id,
                    Review.customer_id == customer_id
                ).first()
            
            if not review:
                review = Review(account_id=account.id)
                db.add(review)
            
            review.customer_name = review_data.get("customer_name")
            review.customer_id = customer_id
            review.rating = review_data.get("rating")
            review.vehicle_info = review_data.get("vehicle_info")
            review.review_text = review_data.get("review_text")
            review.areas_of_improvement = review_data.get("areas_of_improvement", [])
            # Clean the host_response to remove "Your response" prefix
            raw_response = review_data.get("host_response")
            review.host_response = DatabaseService._clean_host_response(raw_response)
            review.has_host_response = bool(review.host_response)
            
            # Link review to vehicle by extracting license plate from vehicle_info
            vehicle_info = review_data.get("vehicle_info")
            if vehicle_info:
                license_plate = None
                # Extract license plate from vehicle_info (format: "Vehicle Name Year • LICENSE-PLATE")
                # Try to match pattern like "• ABC-1234" or "• ABC1234"
                plate_match = re.search(r'•\s*([A-Z0-9-]+)', vehicle_info)
                if plate_match:
                    license_plate = plate_match.group(1)
                else:
                    # Try to extract from end of string (license plate might be last part)
                    parts = vehicle_info.split()
                    if len(parts) > 0:
                        potential_plate = parts[-1]
                        # Check if it looks like a license plate (alphanumeric, 4+ chars)
                        if re.match(r'^[A-Z0-9-]{4,}$', potential_plate):
                            license_plate = potential_plate
                
                if license_plate:
                    # Find vehicle by license plate
                    vehicle = db.query(Vehicle).filter(
                        Vehicle.account_id == account.id,
                        Vehicle.license_plate == license_plate
                    ).first()
                    if vehicle:
                        review.vehicle_id = vehicle.id
                        logger.debug(f"Linked review to vehicle {vehicle.id} via license plate {license_plate}")
            
            # Parse date if provided
            date_str = review_data.get("date")
            if date_str:
                try:
                    review.date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse review date: {date_str}")
            
            
            if DatabaseService._save_entity(db, review, f"review for customer {customer_id or 'unknown'}"):
                saved_reviews.append(review)
        
        logger.info(f"Saved {len(saved_reviews)} reviews for account {account.user_id}")
        return saved_reviews
    
    @staticmethod
    def save_earnings(db: Session, account: Account, earnings_data: Dict[str, Any]) -> tuple[List[EarningsBreakdown], List[VehicleEarnings]]:
        """Save earnings data."""
        saved_breakdowns = []
        saved_vehicle_earnings = []
        
        if earnings_data.get("earnings_breakdown"):
            for breakdown_data in earnings_data["earnings_breakdown"]:
                breakdown = db.query(EarningsBreakdown).filter(
                    EarningsBreakdown.account_id == account.id,
                    EarningsBreakdown.type == breakdown_data.get("type"),
                    EarningsBreakdown.year == breakdown_data.get("year")
                ).first()
                
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
                
                if DatabaseService._save_entity(db, breakdown, f"earnings breakdown {breakdown_data.get('type', 'unknown')}"):
                    saved_breakdowns.append(breakdown)
        
        if earnings_data.get("vehicle_earnings"):
            for vehicle_earnings_data in earnings_data["vehicle_earnings"]:
                vehicle_earnings = None
                year = vehicle_earnings_data.get("year")
                
                # Lookup should include year to find the correct record for each year
                if vehicle_earnings_data.get("license_plate"):
                    vehicle_earnings = db.query(VehicleEarnings).filter(
                        VehicleEarnings.account_id == account.id,
                        VehicleEarnings.license_plate == vehicle_earnings_data.get("license_plate"),
                        VehicleEarnings.year == year
                    ).first()
                
                if not vehicle_earnings and vehicle_earnings_data.get("vehicle_name"):
                    vehicle_earnings = db.query(VehicleEarnings).filter(
                        VehicleEarnings.account_id == account.id,
                        VehicleEarnings.vehicle_name == vehicle_earnings_data.get("vehicle_name"),
                        VehicleEarnings.trim == vehicle_earnings_data.get("trim"),
                        VehicleEarnings.year == year
                    ).first()
                
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
                
                if DatabaseService._save_entity(db, vehicle_earnings, f"vehicle earnings {vehicle_earnings_data.get('vehicle_name', 'unknown')}"):
                    saved_vehicle_earnings.append(vehicle_earnings)
        
        logger.info(f"Saved {len(saved_breakdowns)} earnings breakdowns and {len(saved_vehicle_earnings)} vehicle earnings for account {account.user_id}")
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
        
        logger.info(f"Attempting to save {len(transactions_list)} transactions for account {account.user_id}")
        
        for idx, transaction_data in enumerate(transactions_list, 1):
            logger.debug(f"Processing transaction {idx}/{len(transactions_list)}: {transaction_data.get('type')} | {transaction_data.get('date')} | {transaction_data.get('reservation_id') or 'N/A'}")
            # Try to find existing transaction by unique combination
            # Use reservation_id + date + type + year as unique identifier
            reservation_id = transaction_data.get("reservation_id")
            date = transaction_data.get("date")
            transaction_type = transaction_data.get("type")
            year = transaction_data.get("year")
            
            existing_transaction = None
            
            # If we have a reservation_id, try to link to a vehicle via trip
            vehicle_id = None
            
            if reservation_id:
                # Try to find trip by reservation_id (trip_id in Trip model) to get vehicle_id
                trip = db.query(Trip).filter(
                    Trip.account_id == account.id,
                    Trip.trip_id == reservation_id
                ).first()
                if trip:
                    vehicle_id = trip.vehicle_id
            
            # If we have vehicle_name but no vehicle_id, try to find vehicle
            if not vehicle_id and transaction_data.get("vehicle_name"):
                vehicle = db.query(Vehicle).filter(
                    Vehicle.account_id == account.id,
                    Vehicle.name == transaction_data.get("vehicle_name")
                ).first()
                if vehicle:
                    vehicle_id = vehicle.id
            
            # Look for existing transaction
            if reservation_id and date and transaction_type and year:
                existing_transaction = db.query(Transaction).filter(
                    Transaction.account_id == account.id,
                    Transaction.reservation_id == reservation_id,
                    Transaction.date == date,
                    Transaction.type == transaction_type,
                    Transaction.year == year
                ).first()
            elif date and transaction_type and year:
                # For payments without reservation_id, use date + type + year + payment_details
                existing_transaction = db.query(Transaction).filter(
                    Transaction.account_id == account.id,
                    Transaction.date == date,
                    Transaction.type == transaction_type,
                    Transaction.year == year,
                    Transaction.payment_details == transaction_data.get("payment_details")
                ).first()
            
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
                # Update existing transaction
                existing_transaction.vehicle_id = vehicle_id or existing_transaction.vehicle_id
                existing_transaction.trip_name = transaction_data.get("trip_name") or existing_transaction.trip_name
                existing_transaction.vehicle_name = transaction_data.get("vehicle_name") or existing_transaction.vehicle_name
                existing_transaction.payment_details = transaction_data.get("payment_details") or existing_transaction.payment_details
                existing_transaction.earnings_amount = transaction_data.get("earnings_amount") or existing_transaction.earnings_amount
                existing_transaction.earnings_amount_numeric = transaction_data.get("earnings_amount_numeric") or existing_transaction.earnings_amount_numeric
                existing_transaction.payment_amount = transaction_data.get("payment_amount") or existing_transaction.payment_amount
                existing_transaction.payment_amount_numeric = transaction_data.get("payment_amount_numeric") or existing_transaction.payment_amount_numeric
                logger.info(f"  [{idx}] UPDATED existing transaction: {transaction_type} | {date} | {reservation_id or 'N/A'}")
            
            if DatabaseService._save_entity(db, existing_transaction, f"transaction {reservation_id or date or 'unknown'}"):
                saved_transactions.append(existing_transaction)
                logger.debug(f"  [{idx}] ✓ Saved successfully")
            else:
                logger.warning(f"  [{idx}] ✗ Failed to save transaction: {transaction_type} | {date} | {reservation_id or 'N/A'}")
        
        logger.info(f"Saved {len(saved_transactions)} transactions for account {account.user_id}")
        return saved_transactions
    
    @staticmethod
    def save_scraped_data(db: Session, user_id: int, email: str, scraped_data: Dict[str, Any]) -> bool:
        """Save all scraped data to database."""
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
