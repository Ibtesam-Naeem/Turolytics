# ------------------------------ IMPORTS ------------------------------
"""
Database service for saving scraped data to PostgreSQL.

This service handles the conversion of scraped JSON data into database models
and saves them with proper relationships.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database.models import (
    Account,
    Vehicle,
    Trip,
    Review,
    EarningsBreakdown,
    VehicleEarnings,
    SessionStorage,
)

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ DATABASE SERVICE ------------------------------

class DatabaseService:
    """Service for saving scraped data to the database."""
    
    @staticmethod
    def get_or_create_account(db: Session, account_id: int) -> Account:
        """Get or create an account."""
        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            account = Account(account_id=account_id)
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"Created new account: {account_id}")
        return account
    
    @staticmethod
    def get_existing_trip_ids(db: Session, account_id: int) -> set[str]:
        """Get set of existing trip_ids for an account to avoid re-scraping.
        
        Args:
            db: Database session
            account_id: Account ID
            
        Returns:
            Set of trip_id strings that already exist in the database
        """
        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return set()
        
        trips = db.query(Trip.trip_id).filter(
            Trip.account_id == account.id,
            Trip.trip_id.isnot(None)
        ).all()
        existing_ids = {trip_id[0] for trip_id in trips if trip_id[0]}
        logger.debug(f"Found {len(existing_ids)} existing trip_ids for account {account_id}")
        return existing_ids
    
    @staticmethod
    def get_existing_customer_ids(db: Session, account_id: int) -> set[str]:
        """Get set of existing customer_ids for an account to avoid re-scraping.
        
        Args:
            db: Database session
            account_id: Account ID
            
        Returns:
            Set of customer_id strings that already exist in the database
        """
        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return set()
        
        reviews = db.query(Review.customer_id).filter(
            Review.account_id == account.id,
            Review.customer_id.isnot(None)
        ).all()
        existing_ids = {customer_id[0] for customer_id in reviews if customer_id[0]}
        logger.debug(f"Found {len(existing_ids)} existing customer_ids for account {account_id}")
        return existing_ids
    
    @staticmethod
    def save_vehicles(db: Session, account: Account, vehicles_data: Dict[str, Any]) -> List[Vehicle]:
        """Save vehicles data."""
        if not vehicles_data or "vehicles" not in vehicles_data:
            return []
        
        saved_vehicles = []
        scraped_at = datetime.fromisoformat(vehicles_data.get("scraped_at", datetime.utcnow().isoformat()))
        
        for vehicle_data in vehicles_data.get("vehicles", []):
            try:
                # Find existing vehicle by license plate or create new
                vehicle = None
                if vehicle_data.get("license_plate"):
                    vehicle = db.query(Vehicle).filter(
                        Vehicle.account_id == account.id,
                        Vehicle.license_plate == vehicle_data["license_plate"]
                    ).first()
                
                if not vehicle:
                    vehicle = Vehicle(account_id=account.id)
                    db.add(vehicle)
                
                # Update vehicle data
                vehicle.name = vehicle_data.get("name")
                vehicle.year = vehicle_data.get("year")
                vehicle.trim = vehicle_data.get("trim")
                vehicle.license_plate = vehicle_data.get("license_plate")
                vehicle.status = vehicle_data.get("status")
                vehicle.trip_info = vehicle_data.get("trip_info")
                vehicle.rating = vehicle_data.get("rating")
                vehicle.trip_count = vehicle_data.get("trip_count")
                vehicle.scraped_at = scraped_at
                
                db.commit()
                db.refresh(vehicle)
                saved_vehicles.append(vehicle)
                
            except Exception as e:
                logger.error(f"Error saving vehicle {vehicle_data.get('license_plate')}: {e}")
                db.rollback()
        
        logger.info(f"Saved {len(saved_vehicles)} vehicles for account {account.account_id}")
        return saved_vehicles
    
    @staticmethod
    def save_trips(db: Session, account: Account, trips_data: Dict[str, Any]) -> List[Trip]:
        """Save trips data (both booked and history)."""
        saved_trips = []
        
        booked_trips = trips_data.get("booked_trips", {}).get("trips", [])
        booked_scraped_at = trips_data.get("booked_trips", {}).get("scraped_at")
        if booked_scraped_at:
            booked_scraped_at = datetime.fromisoformat(booked_scraped_at.replace("Z", "+00:00"))
        
        history_trips = trips_data.get("trip_history", {}).get("trips", [])
        history_scraped_at = trips_data.get("trip_history", {}).get("scraped_at")
        if history_scraped_at:
            history_scraped_at = datetime.fromisoformat(history_scraped_at.replace("Z", "+00:00"))
        
        all_trips = []
        for trip_data in booked_trips:
            trip_data["trip_type"] = "booked_trips"
            trip_data["scraped_at"] = booked_scraped_at
            all_trips.append(trip_data)
        
        for trip_data in history_trips:
            trip_data["trip_type"] = "trip_history"
            trip_data["scraped_at"] = history_scraped_at
            all_trips.append(trip_data)
        
        for trip_data in all_trips:
            try:
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
                
                vehicle = None
                if trip_data.get("license_plate"):
                    vehicle = db.query(Vehicle).filter(
                        Vehicle.account_id == account.id,
                        Vehicle.license_plate == trip_data["license_plate"]
                    ).first()
                    if vehicle:
                        trip.vehicle_id = vehicle.id
                
                trip.trip_id = trip_id_str
                trip.reservation_number = trip_data.get("metadata", {}).get("reservation_number")
                trip.trip_url = trip_data.get("trip_url")
                trip.customer_name = trip_data.get("customer_name")
                trip.status = trip_data.get("status")
                trip.trip_type = trip_data.get("trip_type")
                trip.cancellation_info = trip_data.get("cancellation_info")
                trip.cancelled_by = trip_data.get("cancelled_by")
                trip.cancelled_date = trip_data.get("cancelled_date")
                trip.trip_dates = trip_data.get("trip_dates")
                
                schedule_data = trip_data.get("schedule", {})
                trip.start_date = schedule_data.get("start_date")
                trip.start_time = schedule_data.get("start_time")
                trip.end_date = schedule_data.get("end_date")
                trip.end_time = schedule_data.get("end_time")
                
                location_data = trip_data.get("location", {})
                trip.location_type = location_data.get("location_type")
                trip.address = location_data.get("address")
                
                kilometers_data = trip_data.get("kilometers", {})
                trip.kilometers_included = kilometers_data.get("kilometers_included")
                trip.kilometers_driven = kilometers_data.get("kilometers_driven")
                trip.overage_rate = kilometers_data.get("overage_rate")
                
                earnings_data = trip_data.get("earnings", {})
                trip.total_earnings = earnings_data.get("total_earnings")
                trip.receipt_url = earnings_data.get("receipt_url")
                
                protection_data = trip_data.get("protection", {})
                trip.protection_plan = protection_data.get("protection_plan")
                trip.deductible = protection_data.get("deductible")
                
                metadata_data = trip_data.get("metadata", {})
                trip.card_index = metadata_data.get("card_index")
                
                if trip_data.get("scraped_at"):
                    trip.scraped_at = trip_data["scraped_at"]
                
                db.commit()
                db.refresh(trip)
                saved_trips.append(trip)
                
            except Exception as e:
                logger.error(f"Error saving trip {trip_data.get('trip_id')}: {e}")
                db.rollback()
        
        logger.info(f"Saved {len(saved_trips)} trips for account {account.account_id}")
        return saved_trips
    
    @staticmethod
    def save_reviews(db: Session, account: Account, reviews_data: Dict[str, Any]) -> List[Review]:
        """Save reviews data."""
        if not reviews_data or "reviews" not in reviews_data:
            return []
        
        saved_reviews = []
        scraped_at = datetime.fromisoformat(reviews_data.get("summary", {}).get("scraped_at", datetime.utcnow().isoformat()))
        
        for review_data in reviews_data.get("reviews", []):
            try:
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
                
                vehicle = None
                if review_data.get("vehicle_info"):
                    pass
                
                review.customer_name = review_data.get("customer_name")
                review.customer_id = customer_id
                review.rating = review_data.get("rating")
                review.vehicle_info = review_data.get("vehicle_info")
                review.review_text = review_data.get("review_text")
                review.areas_of_improvement = review_data.get("areas_of_improvement", [])
                review.host_response = review_data.get("host_response")
                review.has_host_response = review_data.get("has_host_response", False)
                review.scraped_at = scraped_at
                
                db.commit()
                db.refresh(review)
                saved_reviews.append(review)
                
            except Exception as e:
                logger.error(f"Error saving review for customer {review_data.get('customer_id')}: {e}")
                db.rollback()
        
        logger.info(f"Saved {len(saved_reviews)} reviews for account {account.account_id}")
        return saved_reviews
    
    @staticmethod
    def save_earnings(db: Session, account: Account, earnings_data: Dict[str, Any]) -> tuple[List[EarningsBreakdown], List[VehicleEarnings]]:
        """Save earnings data."""
        saved_breakdowns = []
        saved_vehicle_earnings = []
        
        if earnings_data.get("earnings_breakdown"):
            scraped_at = datetime.utcnow()
            for breakdown_data in earnings_data["earnings_breakdown"]:
                try:
                    breakdown = EarningsBreakdown(
                        account_id=account.id,
                        type=breakdown_data.get("type"),
                        amount=breakdown_data.get("amount"),
                        amount_numeric=DatabaseService._parse_amount(breakdown_data.get("amount")),
                        scraped_at=scraped_at
                    )
                    db.add(breakdown)
                    db.commit()
                    db.refresh(breakdown)
                    saved_breakdowns.append(breakdown)
                except Exception as e:
                    logger.error(f"Error saving earnings breakdown: {e}")
                    db.rollback()
        
        if earnings_data.get("vehicle_earnings"):
            scraped_at = datetime.utcnow()
            for vehicle_earnings_data in earnings_data["vehicle_earnings"]:
                try:
                    vehicle_earnings = VehicleEarnings(
                        account_id=account.id,
                        vehicle_name=vehicle_earnings_data.get("vehicle_name"),
                        license_plate=vehicle_earnings_data.get("license_plate"),
                        trim=vehicle_earnings_data.get("trim"),
                        earnings_amount=vehicle_earnings_data.get("earnings_amount"),
                        earnings_amount_numeric=DatabaseService._parse_amount(vehicle_earnings_data.get("earnings_amount")),
                        scraped_at=scraped_at
                    )
                    db.add(vehicle_earnings)
                    db.commit()
                    db.refresh(vehicle_earnings)
                    saved_vehicle_earnings.append(vehicle_earnings)
                except Exception as e:
                    logger.error(f"Error saving vehicle earnings: {e}")
                    db.rollback()
        
        logger.info(f"Saved {len(saved_breakdowns)} earnings breakdowns and {len(saved_vehicle_earnings)} vehicle earnings for account {account.account_id}")
        return saved_breakdowns, saved_vehicle_earnings
    
    @staticmethod
    def _parse_amount(amount_str: Optional[str]) -> Optional[float]:
        """Parse amount string to float."""
        if not amount_str:
            return None
        try:
            cleaned = amount_str.replace("$", "").replace(",", "").strip()
            return float(cleaned)
        
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def save_scraped_data(db: Session, account_id: int, scraped_data: Dict[str, Any]) -> bool:
        """Save all scraped data to database.
        
        Args:
            db: Database session
            account_id: Account ID
            scraped_data: Dictionary containing all scraped data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = DatabaseService.get_or_create_account(db, account_id)
            
            if "vehicles" in scraped_data:
                DatabaseService.save_vehicles(db, account, scraped_data["vehicles"])
            
            if "trips" in scraped_data:
                DatabaseService.save_trips(db, account, scraped_data["trips"])
            
            if "reviews" in scraped_data:
                DatabaseService.save_reviews(db, account, scraped_data["reviews"])
            
            if "earnings" in scraped_data:
                DatabaseService.save_earnings(db, account, scraped_data["earnings"])
            
            logger.info(f"Successfully saved all scraped data for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scraped data to database: {e}")
            db.rollback()
            return False

# ------------------------------ END OF FILE ------------------------------

