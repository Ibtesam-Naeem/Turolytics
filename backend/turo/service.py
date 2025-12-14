# ------------------------------ IMPORTS ------------------------------
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from datetime import datetime

from core.database.models import Trip, Vehicle, Review, EarningsBreakdown, VehicleEarnings, Account

# ------------------------------ SERVICE ------------------------------

class TuroDataService:
    """Service for retrieving Turo data from the database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _build_base_query(self, model_class, account: Account):
        """Build base query filtered by account."""
        return self.db.query(model_class).filter(model_class.account_id == account.id)
    
    def get_trips(
        self,
        account: Account,
        trip_id: Optional[str] = None,
        status: Optional[str] = None,
        trip_type: Optional[str] = None,
        vehicle_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Trip], int]:
        """Get trips with filtering and pagination."""
        query = self._build_base_query(Trip, account)
        
        if trip_id:
            query = query.filter(Trip.trip_id == trip_id)
        if status:
            query = query.filter(Trip.status == status)
        if trip_type:
            query = query.filter(Trip.trip_type == trip_type)
        if vehicle_id:
            query = query.filter(Trip.vehicle_id == vehicle_id)
        if start_date:
            query = query.filter(Trip.created_at >= start_date)
        if end_date:
            query = query.filter(Trip.created_at <= end_date)
        
        total = query.count()
        trips = query.order_by(desc(Trip.created_at)).limit(limit).offset(offset).all()
        
        return trips, total
    
    def get_vehicles(
        self,
        account: Account,
        vehicle_id: Optional[int] = None,
        license_plate: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Vehicle], int]:
        """Get vehicles with filtering and pagination."""
        query = self._build_base_query(Vehicle, account)
        
        if vehicle_id:
            query = query.filter(Vehicle.id == vehicle_id)
        if license_plate:
            query = query.filter(Vehicle.license_plate == license_plate)
        if status:
            query = query.filter(Vehicle.status == status)
        
        total = query.count()
        vehicles = query.order_by(desc(Vehicle.created_at)).limit(limit).offset(offset).all()
        
        return vehicles, total
    
    def get_reviews(
        self,
        account: Account,
        review_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        has_response: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Review], int]:
        """Get reviews with filtering and pagination."""
        query = self._build_base_query(Review, account)
        
        if review_id:
            query = query.filter(Review.id == review_id)
        if vehicle_id:
            query = query.filter(Review.vehicle_id == vehicle_id)
        if min_rating is not None:
            query = query.filter(Review.rating >= min_rating)
        if has_response is not None:
            query = query.filter(Review.has_host_response == has_response)
        
        order_rule = case(
            (Review.date != None, Review.date),
            else_=Review.created_at
        )
        
        total = query.count()
        reviews = query.order_by(desc(order_rule)).limit(limit).offset(offset).all()
        
        return reviews, total
    
    def get_earnings(
        self,
        account: Account,
        year: Optional[int] = None
    ) -> Tuple[List[EarningsBreakdown], List[VehicleEarnings]]:
        """Get earnings data."""
        breakdown_query = self._build_base_query(EarningsBreakdown, account)
        vehicle_earnings_query = self._build_base_query(VehicleEarnings, account)
        
        if year:
            breakdown_query = breakdown_query.filter(EarningsBreakdown.year == str(year))
        
        breakdowns = breakdown_query.all()
        vehicle_earnings = vehicle_earnings_query.all()
        
        return breakdowns, vehicle_earnings
    
# ------------------------------ END OF FILE ------------------------------

