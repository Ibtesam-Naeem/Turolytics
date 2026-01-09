# ------------------------------ IMPORTS ------------------------------
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, func, or_, and_
from datetime import datetime, timezone, timedelta
from calendar import monthrange
import re

from core.database.models import Trip, Vehicle, Review, EarningsBreakdown, VehicleEarnings, VehicleUtilizationHistory, Account, BouncieVehicleMapping, VehicleOdometerHistory
from . import parsing

# ------------------------------ HELPER FUNCTIONS ------------------------------

def get_trip_url(trip_id: str) -> str:
    """Generate Turo trip URL from trip_id."""
    return f"https://turo.com/us/en/reservation/{trip_id}"

def get_receipt_url(trip_id: str) -> str:
    """Generate Turo receipt URL from trip_id."""
    return f"https://turo.com/us/en/reservation/{trip_id}/receipt"

# Month names constant
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# ------------------------------ SERVICE ------------------------------

class TuroDataService:
    """Service for retrieving Turo data from the database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _build_base_query(self, model_class, account: Account):
        """Build base query filtered by account."""
        return self.db.query(model_class).filter(model_class.account_id == account.id)
    
    def _get_vehicle_name(self, trip: Trip) -> str:
        """Get vehicle name for a trip, with caching to avoid N+1 queries."""
        if not trip.vehicle_id:
            return "Unknown Vehicle"
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
        return vehicle.name if vehicle else "Unknown Vehicle"
    
    def _is_completed_or_cancelled(self, trip: Trip) -> bool:
        """Check if trip is completed or cancelled."""
        if not trip.status:
            return False
        status_upper = trip.status.upper()
        return any(s in status_upper for s in ['COMPLETED', 'CANCELLED', 'CANCELED'])
    
    def _parse_date_with_timezone(self, date_str: Optional[str], year: Optional[int] = None, updated_at: Optional[datetime] = None) -> Optional[datetime]:
        """Parse date string and ensure timezone awareness.
        
        Handles year rollover: if parsed date is in the past but updated_at is recent,
        assumes it's in the next year (for upcoming trips crossing year boundary).
        """
        if not date_str:
            return None
        
        parsed_date = parsing._parse_turo_date(date_str, year)
        if not parsed_date:
            return None
        
        # Use updated_at year if available for better accuracy
        reference_date = None
        if updated_at and not year:
            try:
                updated_year = updated_at.year
                parsed_date = parsing._parse_turo_date(date_str, updated_year)
                # Ensure reference_date is timezone-aware
                if updated_at.tzinfo:
                    reference_date = updated_at
                else:
                    reference_date = updated_at.replace(tzinfo=timezone.utc)
            except:
                pass
        
        # Handle year rollover for upcoming trips
        # If parsed date is in the past but updated_at is recent, try next year
        if parsed_date and reference_date:
            today = datetime.now(timezone.utc)
            parsed_date_tz = parsed_date.replace(tzinfo=timezone.utc) if parsed_date.tzinfo is None else parsed_date
            
            # If parsed date is in the past and updated_at is recent (within last 90 days),
            # it might be a year rollover case (e.g., "Jan 02" scraped in December)
            if parsed_date_tz.date() < today.date():
                days_since_updated = (today - reference_date).days
                if days_since_updated < 90:
                    # Try next year
                    next_year_date = parsed_date.replace(year=parsed_date.year + 1)
                    next_year_date_tz = next_year_date.replace(tzinfo=timezone.utc) if next_year_date.tzinfo is None else next_year_date
                    # If next year date is in the future, use it
                    if next_year_date_tz.date() >= today.date():
                        parsed_date = next_year_date
        
        if parsed_date and parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        
        return parsed_date
    
    def _get_vehicle_year(self, vehicle: Vehicle) -> int:
        """Extract vehicle year from vehicle object."""
        if vehicle.year:
            try:
                return int(vehicle.year)
            except (ValueError, TypeError):
                pass
        
        # Try to parse year from name (e.g., "2024 Tesla Model 3")
        if vehicle.name:
            year_match = re.search(r'\b(19|20)\d{2}\b', vehicle.name)
            if year_match:
                return int(year_match.group())
        
        return datetime.now().year
    
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
            (Review.date.isnot(None), Review.date),
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
            vehicle_earnings_query = vehicle_earnings_query.filter(VehicleEarnings.year == str(year))
        
        breakdowns = breakdown_query.all()
        vehicle_earnings = vehicle_earnings_query.all()
        
        return breakdowns, vehicle_earnings
    
    def _is_date_today(self, date_str: Optional[str]) -> bool:
        """Check if a date string represents today."""
        parsed_date = self._parse_date_with_timezone(date_str)
        if not parsed_date:
            return False
        return parsed_date.date() == datetime.now(timezone.utc).date()
    
    def _calculate_vehicle_utilization(
        self,
        vehicle_id: int,
        account: Account,
        period_days: int = 30,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        reference_year: Optional[int] = None
    ) -> Tuple[float, int, int]:
        """
        Calculate vehicle utilization for a standard period (default: last 30 days).
        
        Utilization = (unique booked days / total days in period) * 100
        
        Args:
            vehicle_id: Vehicle ID to calculate utilization for
            account: Account object
            period_days: Number of days for the period (default: 30)
            period_start: Start of period (defaults to period_days ago)
            period_end: End of period (defaults to today)
        
        Returns:
            Tuple of (utilization percentage (0-100), booked_days, total_days)
        """
        # Default period: last N days (standardized period)
        if period_end is None:
            period_end = datetime.now(timezone.utc)
        
        # Get vehicle
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.account_id == account.id
        ).first()
        
        if not vehicle:
            return (0.0, 0, period_days)
        
        # Use standard period: last N days (not vehicle creation date)
        if period_start is None:
            period_start = period_end - timedelta(days=period_days)
            # Ensure timezone-aware
            if period_start.tzinfo is None:
                period_start = period_start.replace(tzinfo=timezone.utc)
        
        # Adjust period_start if vehicle has a listed_on_turo_date and it's after period_start
        if vehicle.listed_on_turo_date:
            # If the period starts before the vehicle was listed, adjust it
            if period_start < vehicle.listed_on_turo_date:
                period_start = vehicle.listed_on_turo_date
                # If period_start is now after period_end, return 0 utilization
                if period_start > period_end:
                    return (0.0, 0, 0)
        
        # Adjust period_end if vehicle has a removed_from_turo_date and it's before period_end
        if vehicle.removed_from_turo_date:
            # If the period ends after the vehicle was removed, adjust it
            if period_end > vehicle.removed_from_turo_date:
                period_end = vehicle.removed_from_turo_date
                # If period_start is now after period_end, return 0 utilization
                if period_start > period_end:
                    return (0.0, 0, 0)
        
        # Get all trips for this vehicle (excluding cancelled)
        trips = self.db.query(Trip).filter(
            Trip.vehicle_id == vehicle_id,
            Trip.account_id == account.id,
            ~Trip.status.in_(['CANCELLED', 'CANCELED'])
        ).all()
        
        # Build set of unique booked dates
        booked_dates = set()
        period_start_date = period_start.date()
        period_end_date = period_end.date()
        
        if not trips:
            total_days = (period_end_date - period_start_date).days + 1
            return (0.0, 0, total_days)
        
        for trip in trips:
            # Use reference_year if provided (for monthly calculations), otherwise let parser infer from updated_at
            start_date_obj = self._parse_date_with_timezone(trip.start_date, year=reference_year, updated_at=trip.updated_at)
            end_date_obj = self._parse_date_with_timezone(trip.end_date, year=reference_year, updated_at=trip.updated_at)
            
            # If we have both dates, add all days in range
            if start_date_obj and end_date_obj:
                start_date = start_date_obj.date()
                end_date = end_date_obj.date()
                
                # Only count dates within the period
                current = max(start_date, period_start_date)
                end_date_clamped = min(end_date, period_end_date)
                
                # Add all dates in range (inclusive)
                while current <= end_date_clamped:
                    booked_dates.add(current)
                    current += timedelta(days=1)
            elif start_date_obj:
                # If only start date, count as 1 day
                start_date = start_date_obj.date()
                if period_start_date <= start_date <= period_end_date:
                    booked_dates.add(start_date)
        
        # Calculate utilization
        total_days = (period_end_date - period_start_date).days + 1
        if total_days <= 0:
            return (0.0, 0, total_days)
        
        booked_days = len(booked_dates)
        utilization = (booked_days / total_days) * 100
        
        # Clamp between 0 and 100
        return (min(100.0, max(0.0, utilization)), booked_days, total_days)
    
    def _calculate_monthly_utilization(
        self,
        vehicle_id: int,
        account: Account,
        year: int,
        month: int
    ) -> Tuple[float, int, int]:
        """
        Calculate vehicle utilization for a specific month.
        
        Utilization = (days booked in month / total days in month) * 100
        
        Args:
            vehicle_id: Vehicle ID to calculate utilization for
            account: Account object
            year: Year (e.g., 2025)
            month: Month (1-12)
        
        Returns:
            Tuple of (utilization percentage (0-100), booked_days, total_days)
        """
        # Get month boundaries
        month_start = datetime(year, month, 1, tzinfo=timezone.utc)
        _, last_day = monthrange(year, month)
        month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        
        # Check if vehicle was listed before this month
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.account_id == account.id
        ).first()
        
        if vehicle and vehicle.listed_on_turo_date:
            # If vehicle was listed after the end of this month, exclude it
            # (If listed during or before the month, include it)
            if vehicle.listed_on_turo_date > month_end:
                # Vehicle wasn't listed yet, return 0 with 0 total days
                return (0.0, 0, 0)
        
        # Check if vehicle was removed before or during this month
        if vehicle and vehicle.removed_from_turo_date:
            # If vehicle was removed before the start of this month, exclude it
            if vehicle.removed_from_turo_date < month_start:
                # Vehicle was removed before this month, return 0 with 0 total days
                return (0.0, 0, 0)
            # If vehicle was removed during this month, adjust month_end
            if vehicle.removed_from_turo_date < month_end:
                month_end = vehicle.removed_from_turo_date
        
        # Use the existing calculation method with month boundaries and pass the year for date parsing
        return self._calculate_vehicle_utilization(
            vehicle_id=vehicle_id,
            account=account,
            period_start=month_start,
            period_end=month_end,
            reference_year=year
        )
    
    def get_monthly_utilization(
        self,
        account: Account,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly utilization data for all vehicles from stored VehicleUtilizationHistory.
        Returns utilization per month with vehicle breakdown.
        
        Args:
            account: Account object
            year: Year to get data for (defaults to current year)
        
        Returns:
            List of month data with utilization and vehicle breakdown
        """
        if year is None:
            year = datetime.now(timezone.utc).year
        
        # Get stored utilization history for this year
        history_records = self.db.query(VehicleUtilizationHistory).filter(
            VehicleUtilizationHistory.account_id == account.id,
            VehicleUtilizationHistory.year == year
        ).all()
        
        # Get all vehicles for trip counting
        vehicles = self.db.query(Vehicle).filter(
            Vehicle.account_id == account.id
        ).all()
        vehicle_map = {v.id: v for v in vehicles}
        
        # Get trips for trip counting (needed for vehicle breakdown)
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            ~Trip.status.in_(['CANCELLED', 'CANCELED'])
        ).all()
        
        # Get current date to determine if we should include future months
        now = datetime.now(timezone.utc)
        current_year = now.year
        current_month = now.month
        
        # Group history records by month
        monthly_data = {}
        
        for month in range(1, 13):
            month_key = MONTH_NAMES[month - 1]
            month_start = datetime(year, month, 1, tzinfo=timezone.utc)
            _, last_day = monthrange(year, month)
            month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            
            # Skip future months (beyond current month if current year)
            if year == current_year and month > current_month:
                continue
            
            # Get utilization records for this month
            month_records = [
                r for r in history_records 
                if r.month == month
            ]
            
            # Build vehicle breakdown from stored data
            vehicle_utilizations = []
            for record in month_records:
                vehicle = vehicle_map.get(record.vehicle_id)
                if not vehicle:
                    continue
                
                # Determine if vehicle was active during this month
                # Vehicle is active if:
                # 1. It was listed on or before the end of this month
                # 2. It was not removed before the start of this month (or has no removal date)
                
                # Check if vehicle was listed by the end of this month
                if vehicle.listed_on_turo_date and vehicle.listed_on_turo_date > month_end:
                    continue  # Vehicle wasn't listed yet
                
                # Check if vehicle was removed before the start of this month
                if vehicle.removed_from_turo_date and vehicle.removed_from_turo_date < month_start:
                    continue  # Vehicle was already removed
                
                # Count trips for this vehicle in this month (for display)
                vehicle_trip_count = len([
                    t for t in trips
                    if t.vehicle_id == record.vehicle_id and
                    self._parse_date_with_timezone(t.start_date, year=year) and
                    month_start <= self._parse_date_with_timezone(t.start_date, year=year).replace(tzinfo=timezone.utc) <= month_end
                ])
                
                vehicle_utilizations.append({
                    'vehicle': vehicle.name,
                    'utilization': round(record.utilization, 1),
                    'trips': vehicle_trip_count,
                    'daysRented': record.booked_days,
                    'totalDays': record.total_days,
                })
            
            # Only include months where at least one vehicle was active
            if vehicle_utilizations:
                # Calculate fleet average utilization (average of all vehicle utilizations)
                fleet_utilization = sum(v['utilization'] for v in vehicle_utilizations) / len(vehicle_utilizations)
                fleet_utilization = min(100.0, max(0.0, fleet_utilization))
                
                monthly_data[month_key] = {
                    'month': month_key,
                    'utilization': round(fleet_utilization, 1),
                    'vehicles': vehicle_utilizations,
                }
        
        # Return as list ordered by month, only including months where vehicles were active
        return [monthly_data[month] for month in MONTH_NAMES if month in monthly_data]
    
    def get_trips_today(
        self,
        account: Account
    ) -> List[Dict[str, Any]]:
        """
        Get trips that are scheduled/booked for today.
        These are trips where the start_date is today, regardless of whether they've started or not.
        Excludes completed and cancelled trips.
        """
        today = datetime.now(timezone.utc).date()
        
        # Get trips for the account, excluding completed/cancelled
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            ~Trip.status.in_(['COMPLETED', 'CANCELLED', 'CANCELED'])
        ).all()
        
        trips_today = []
        for trip in trips:
            if trip.start_date and self._is_date_today(trip.start_date):
                trips_today.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': self._get_vehicle_name(trip),
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'location': trip.location or trip.location_type or 'Unknown Location',
                    'status': trip.status or 'Active',
                    'start_date': trip.start_date,
                    'start_time': trip.start_time,
                })
        
        return trips_today
    
    def get_new_bookings_today(
        self,
        account: Account
    ) -> List[Dict[str, Any]]:
        """
        Get new bookings created today.
        These are upcoming trips that were scraped today (new bookings discovered today).
        Since we only scrape new trips, trips scraped today = new bookings today.
        """
        today = datetime.now(timezone.utc).date()
        
        # Get upcoming trips that were scraped today, excluding completed/cancelled
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            func.date(Trip.updated_at) == today,
            Trip.trip_type == 'booked_trips',
            ~Trip.status.in_(['COMPLETED', 'CANCELLED', 'CANCELED'])
        ).all()
        
        new_bookings = []
        for trip in trips:
            # Parse dates for display
            if trip.start_date and trip.end_date:
                dates_str = f"{trip.start_date} - {trip.end_date}"
            elif trip.start_date:
                dates_str = trip.start_date
            else:
                dates_str = "TBD"
            
            # Get earnings if available
            earnings_str = f"${trip.total_earnings:,.0f}" if trip.total_earnings else "$0"
            
            new_bookings.append({
                'id': trip.id,
                'trip_id': trip.trip_id,
                'guest_name': trip.customer_name or 'Unknown Guest',
                'vehicle_name': self._get_vehicle_name(trip),
                'dates': dates_str,
                'amount': earnings_str,
                'created_at': trip.updated_at.isoformat() if trip.updated_at else None,
            })
        
        return new_bookings
    
    def get_checkouts_today(
        self,
        account: Account
    ) -> List[Dict[str, Any]]:
        """
        Get checkouts happening today (trips ending today).
        These are trips where the end_date is today.
        """
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id
        ).all()
        
        checkouts_today = []
        for trip in trips:
            if trip.end_date and self._is_date_today(trip.end_date):
                checkouts_today.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': self._get_vehicle_name(trip),
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'time': trip.end_time or 'TBD',
                    'location': trip.location or trip.location_type or 'Unknown Location',
                    'end_date': trip.end_date,
                    'end_time': trip.end_time,
                })
        
        return checkouts_today
    
    def get_upcoming_trips(
        self,
        account: Account,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming trips (trips with start_date in the future).
        Returns trips that are not completed or cancelled and have a future start date.
        """
        today = datetime.now(timezone.utc).date()
        
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            ~Trip.status.in_(['COMPLETED', 'CANCELLED', 'CANCELED'])
        ).all()
        
        upcoming_trips = []
        for trip in trips:
            is_upcoming = False
            if trip.start_date:
                parsed_start = self._parse_date_with_timezone(trip.start_date, updated_at=trip.updated_at)
                if parsed_start and parsed_start.date() >= today:
                    is_upcoming = True
                elif not parsed_start:
                    # If we can't parse the date, check trip_type
                    trip_type = (trip.trip_type or '').lower()
                    if 'booked' in trip_type:
                        is_upcoming = True
            else:
                # If no start_date, check trip_type
                trip_type = (trip.trip_type or '').lower()
                if 'booked' in trip_type:
                    is_upcoming = True
            
            if is_upcoming:
                start_date_display = trip.start_date or "TBD"
                if trip.start_time:
                    start_date_display = f"{start_date_display}, {trip.start_time}"
                
                location = trip.location or trip.location_type or "Location TBD"
                
                upcoming_trips.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': self._get_vehicle_name(trip),
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'pickup_location': location,
                    'dropoff_location': location,
                    'earnings': trip.total_earnings or 0,
                    'kms_allowed': trip.kilometers_included or 0,
                    'start_date': start_date_display,
                    'start_date_raw': trip.start_date,
                    'start_time': trip.start_time,
                    'end_date': trip.end_date,
                    'end_time': trip.end_time,
                    'status': trip.status,
                })
        
        # Sort by start date (earliest first)
        upcoming_trips.sort(key=lambda x: (
            self._parse_date_with_timezone(x.get('start_date_raw', '')) or datetime.max.replace(tzinfo=timezone.utc)
        ))
        
        return upcoming_trips[:limit]
    
    def get_current_trips(
        self,
        account: Account,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get current/active trips (trips that are happening right now).
        These are trips that have started (start_date is today or in the past)
        and haven't ended yet (end_date is today or in the future, or no end_date).
        """
        today = datetime.now(timezone.utc).date()
        
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            ~Trip.status.in_(['COMPLETED', 'CANCELLED', 'CANCELED'])
        ).all()
        
        current_trips = []
        for trip in trips:
            # Check start_date - should be today or in the past
            start_date_valid = False
            if trip.start_date:
                parsed_start = self._parse_date_with_timezone(trip.start_date, updated_at=trip.updated_at)
                if parsed_start and parsed_start.date() <= today:
                    start_date_valid = True
                elif not parsed_start:
                    # If we can't parse, assume it's valid if trip_type is booked_trips
                    trip_type = (trip.trip_type or '').lower()
                    if 'booked' in trip_type:
                        start_date_valid = True
            else:
                # If no start_date, check if trip was created recently (within last 7 days)
                if trip.created_at:
                    days_ago = (datetime.now(timezone.utc) - trip.created_at).days
                    if days_ago <= 7:
                        start_date_valid = True
            
            # Check end_date - should be today or in the future (or not set)
            end_date_valid = True
            if trip.end_date:
                parsed_end = self._parse_date_with_timezone(trip.end_date, updated_at=trip.updated_at)
                if parsed_end and parsed_end.date() < today:
                    end_date_valid = False
            
            # Check if trip is currently active
            trip_type = (trip.trip_type or '').lower()
            is_current = (('booked' in trip_type and start_date_valid) or 
                         (start_date_valid and end_date_valid))
            
            if is_current:
                # Get vehicle info
                vehicle = None
                if trip.vehicle_id:
                    vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                
                vehicle_name = vehicle.name if vehicle else "Unknown Vehicle"
                vehicle_year = self._get_vehicle_year(vehicle) if vehicle else datetime.now().year
                
                # Determine status
                status_upper = (trip.status or '').upper()
                if any(s in status_upper for s in ['IN_PROGRESS', 'ACTIVE', 'ONGOING']):
                    status = "Moving"
                elif any(s in status_upper for s in ['PARKED', 'STOPPED']):
                    status = "Parked"
                else:
                    status = "Active"
                
                current_trips.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': vehicle_name,
                    'vehicle_year': vehicle_year,
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'location': trip.address or trip.location_type or "Location TBD",
                    'coordinates': "N/A",
                    'fuel_percent': None,
                    'speed': 0,
                    'status': status,
                    'kms_driven': trip.kilometers_driven or 0,
                    'kms_allowed': trip.kilometers_included or 0,
                    'earnings': trip.total_earnings or 0,
                    'top_speed': 0,
                    'start_date': trip.start_date,
                    'start_time': trip.start_time,
                    'end_date': trip.end_date,
                    'end_time': trip.end_time,
                })
        
        # Sort by start date (most recent first)
        current_trips.sort(key=lambda x: (
            self._parse_date_with_timezone(x.get('start_date', '')) or datetime.min.replace(tzinfo=timezone.utc)
        ), reverse=True)
        
        return current_trips[:limit]
    
    async def get_vehicles_with_stats(
        self,
        account: Account,
        vehicle_id: Optional[int] = None,
        license_plate: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get vehicles with aggregated statistics (revenue, trips, ratings, odometer).
        Returns list of dictionaries with vehicle data and stats.
        """
        # Base vehicle query
        query = self._build_base_query(Vehicle, account)
        
        if vehicle_id:
            query = query.filter(Vehicle.id == vehicle_id)
        if license_plate:
            query = query.filter(Vehicle.license_plate == license_plate)
        if status:
            query = query.filter(Vehicle.status == status)
        
        total = query.count()
        vehicles = query.order_by(desc(Vehicle.created_at)).limit(limit).offset(offset).all()
        
        # Aggregate stats for each vehicle
        vehicles_with_stats = []
        for vehicle in vehicles:
            # Get trip statistics - count only completed trips (exclude cancelled)
            trips_query = self.db.query(
                func.count(Trip.id).label('total_trips')
            ).filter(
                Trip.account_id == account.id,
                Trip.vehicle_id == vehicle.id,
                # Only count completed trips - exclude cancelled
                func.upper(Trip.status).like('%COMPLETED%')
            )
            
            trip_stats = trips_query.first()
            total_trips = trip_stats.total_trips or 0
            
            # Get odometer from Bouncie (preferred) or fallback to trip sum
            total_odometer = await self._get_vehicle_odometer(vehicle, account)
            
            # Get revenue from VehicleEarnings (sum across all years: 2025 + 2026 + ...)
            # Use vehicle_id foreign key (preferred) OR fallback to license_plate/vehicle_name matching
            revenue_query = self.db.query(
                func.sum(VehicleEarnings.earnings_amount_numeric).label('total_revenue')
            ).filter(
                VehicleEarnings.account_id == account.id,
                VehicleEarnings.earnings_amount_numeric.isnot(None)
            )
            
            # Build matching conditions: vehicle_id (preferred) OR license_plate/vehicle_name fallback
            matching_conditions = []
            
            # Primary: Match by vehicle_id if available
            matching_conditions.append(VehicleEarnings.vehicle_id == vehicle.id)
            
            # Fallback: Match by license_plate if vehicle_id is NULL
            if vehicle.license_plate:
                matching_conditions.append(
                    and_(
                        VehicleEarnings.vehicle_id.is_(None),
                        VehicleEarnings.license_plate == vehicle.license_plate
                    )
                )
            
            # Fallback: Match by vehicle_name + trim if vehicle_id is NULL and no license_plate match
            if vehicle.name:
                name_conditions = [
                    VehicleEarnings.vehicle_id.is_(None),
                    VehicleEarnings.vehicle_name == vehicle.name
                ]
                if vehicle.trim:
                    name_conditions.append(VehicleEarnings.trim == vehicle.trim)
                matching_conditions.append(and_(*name_conditions))
            
            # Apply OR logic to match by any condition
            if matching_conditions:
                revenue_query = revenue_query.filter(or_(*matching_conditions))
            
            revenue_stats = revenue_query.first()
            total_revenue = float(revenue_stats.total_revenue or 0) if revenue_stats and revenue_stats.total_revenue else 0.0
            
            # Get review statistics (average rating)
            reviews_query = self.db.query(
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.id).label('review_count')
            ).filter(
                Review.account_id == account.id,
                Review.vehicle_id == vehicle.id,
                Review.rating.isnot(None)
            )
            
            review_stats = reviews_query.first()
            avg_rating = float(review_stats.avg_rating) if review_stats.avg_rating else None
            review_count = review_stats.review_count or 0
            
            # Use vehicle's rating if no reviews, or average of reviews if available
            final_rating = avg_rating if avg_rating else vehicle.rating
            
            # Get utilization from monthly history - use most recent month with data
            now = datetime.now(timezone.utc)
            current_year = now.year
            current_month = now.month
            
            # Try to get current month's utilization from history
            current_month_history = self.db.query(VehicleUtilizationHistory).filter(
                VehicleUtilizationHistory.vehicle_id == vehicle.id,
                VehicleUtilizationHistory.account_id == account.id,
                VehicleUtilizationHistory.year == current_year,
                VehicleUtilizationHistory.month == current_month
            ).first()
            
            if current_month_history:
                # Use current month's stored utilization
                utilization_value = current_month_history.utilization
                booked_days = current_month_history.booked_days
                total_days = current_month_history.total_days
            else:
                # No history for current month - calculate it on the fly
                utilization_value, booked_days, total_days = self._calculate_monthly_utilization(
                    vehicle_id=vehicle.id,
                    account=account,
                    year=current_year,
                    month=current_month
                )
                
                # Create history record for current month (will be committed by caller)
                history_record = VehicleUtilizationHistory(
                    vehicle_id=vehicle.id,
                    account_id=account.id,
                    year=current_year,
                    month=current_month,
                    booked_days=booked_days,
                    total_days=total_days,
                    calculated_at=now
                )
                self.db.add(history_record)
            
            # Map status to frontend format
            status_mapped = self._map_vehicle_status(vehicle.status)
            
            # Build vehicle dict with stats
            vehicle_dict = {
                'id': vehicle.id,
                'name': vehicle.name,
                'year': vehicle.year,
                'trim': vehicle.trim,
                'license_plate': vehicle.license_plate,
                'status': vehicle.status,
                'status_mapped': status_mapped,
                'trip_info': vehicle.trip_info,
                'rating': final_rating,
                'trip_count': vehicle.trip_count or total_trips,
                'listed_on_turo_date': vehicle.listed_on_turo_date,
                'removed_from_turo_date': vehicle.removed_from_turo_date,
                'utilization_goal': vehicle.utilization_goal,
                'created_at': vehicle.created_at,
                'updated_at': vehicle.updated_at,
                'total_revenue': total_revenue,
                'total_odometer': total_odometer,
                'total_trips': total_trips,
                'avg_rating': final_rating,
                'review_count': review_count,
                'utilization': round(utilization_value, 1) if utilization_value is not None else 0.0,
            }
            
            vehicles_with_stats.append(vehicle_dict)
        
        return vehicles_with_stats, total
    
    async def _get_vehicle_odometer(self, vehicle: Vehicle, account: Account) -> int:
        """
        Get vehicle odometer reading.
        Priority:
        1. Current odometer from Bouncie API (if vehicle is mapped) - real-time
        2. Latest daily snapshot from VehicleOdometerHistory
        3. Return 0 if no odometer data available (do NOT use trip sum)
        """
        # Check if vehicle has Bouncie mapping
        mapping = self.db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.vehicle_id == vehicle.id,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        # Try to get current odometer from Bouncie API if mapped
        if mapping and mapping.imei:
            try:
                from bouncie.service import BouncieService
                import logging
                logger = logging.getLogger(__name__)
                
                service = BouncieService(db=self.db, account_id=account.id)
                
                if service.access_token:
                    # Get vehicles from Bouncie (we're in async context, so use await)
                    logger.info(f"Fetching Bouncie odometer for vehicle {vehicle.id} (IMEI: {mapping.imei})")
                    vehicles_result = await service.get_vehicles()
                    
                    if vehicles_result and vehicles_result.get("success"):
                        bouncie_vehicles = vehicles_result.get("data", []) or []
                        logger.info(f"Found {len(bouncie_vehicles)} vehicles from Bouncie API")
                        # Find vehicle by IMEI
                        for bv in bouncie_vehicles:
                            if bv.get("imei") == mapping.imei:
                                stats = bv.get('stats', {})
                                if isinstance(stats, dict):
                                    odometer_miles = stats.get('odometer')
                                    if odometer_miles is not None:
                                        # Convert miles to kilometers
                                        odometer_km = int(float(odometer_miles) * 1.60934)
                                        logger.info(f"✓ Using Bouncie odometer: {odometer_miles} miles = {odometer_km:,} km for vehicle {vehicle.id}")
                                        return odometer_km
                                    else:
                                        logger.warning(f"No odometer value in stats for vehicle {vehicle.id}, IMEI {mapping.imei}")
                                else:
                                    logger.warning(f"Stats is not a dict for vehicle {vehicle.id}: {type(stats)}")
                        logger.warning(f"Vehicle with IMEI {mapping.imei} not found in Bouncie response for vehicle {vehicle.id}")
                    else:
                        logger.warning(f"Bouncie API call failed: {vehicles_result.get('error') if vehicles_result else 'No result'}")
                else:
                    logger.debug(f"No Bouncie access token for vehicle {vehicle.id}")
            except Exception as e:
                # Log but don't fail - fall through to other methods
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Exception getting odometer from Bouncie API for vehicle {vehicle.id}: {e}", exc_info=True)
        
        # Try to get latest odometer from daily history
        latest_snapshot = self.db.query(VehicleOdometerHistory).filter(
            VehicleOdometerHistory.vehicle_id == vehicle.id,
            VehicleOdometerHistory.account_id == account.id
        ).order_by(VehicleOdometerHistory.date.desc()).first()
        
        if latest_snapshot:
            # Convert miles to kilometers
            return int(latest_snapshot.odometer_miles * 1.60934)
        
        # No odometer data available - return 0 (do NOT use trip sum)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"No odometer data available for vehicle {vehicle.id} ({vehicle.name}) - returning 0")
        return 0
    
    def _map_vehicle_status(self, status: Optional[str]) -> str:
        """Map Turo vehicle status to frontend status format."""
        if not status:
            return "inactive"
        
        status_lower = status.lower()
        if "listed" in status_lower or "active" in status_lower:
            return "active"
        elif "snoozed" in status_lower or "maintenance" in status_lower:
            return "maintenance"
        else:
            return "inactive"
    
    def get_monthly_revenue(
        self,
        account: Account,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly revenue data from completed trips.
        Returns revenue per month for the specified year.
        
        Args:
            account: Account object
            year: Year to get data for (defaults to current year)
        
        Returns:
            List of month data with revenue
        """
        if year is None:
            year = datetime.now(timezone.utc).year
        
        # Get all completed trips for the account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.status.in_(['COMPLETED'])
        ).all()
        
        # Group revenue by month
        monthly_data = {}
        
        for month in range(1, 13):
            month_key = MONTH_NAMES[month - 1]
            month_start = datetime(year, month, 1, tzinfo=timezone.utc)
            _, last_day = monthrange(year, month)
            month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            
            # Calculate revenue for this month from trips
            month_revenue = 0.0
            for trip in trips:
                # Check if trip end_date falls in this month
                if trip.end_date:
                    parsed_end = self._parse_date_with_timezone(trip.end_date, year=year)
                    if parsed_end and month_start <= parsed_end <= month_end:
                        month_revenue += float(trip.total_earnings or 0)
                # Also check start_date if end_date is not available
                elif trip.start_date:
                    parsed_start = self._parse_date_with_timezone(trip.start_date, year=year)
                    if parsed_start and month_start <= parsed_start <= month_end:
                        month_revenue += float(trip.total_earnings or 0)
            
            # Always include all months, even if revenue is 0
            monthly_data[month_key] = {
                'month': month_key,
                'revenue': round(month_revenue, 2),
            }
        
        # Return as list ordered by month, including all 12 months
        return [monthly_data[month] for month in MONTH_NAMES]
    
    async def get_top_performing_vehicles(
        self,
        account: Account,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top performing vehicles ranked by revenue.
        Returns list of vehicles with revenue, utilization, rating, and trip count.
        """
        # Get all vehicles with stats
        vehicles_data, _ = await self.get_vehicles_with_stats(
            account=account,
            limit=1000,  # Get all vehicles to calculate rankings
            offset=0
        )
        
        top_vehicles = []
        for vehicle_data in vehicles_data:
            vehicle_id = vehicle_data.get('id')
            if not vehicle_id:
                continue
            
            # Get utilization from vehicle_data (already calculated in get_vehicles_with_stats)
            utilization = vehicle_data.get('utilization', 0.0) or 0.0
            
            # Only include vehicles with revenue
            revenue = vehicle_data.get('total_revenue', 0) or 0
            if revenue > 0:
                rating = vehicle_data.get('avg_rating') or vehicle_data.get('rating') or 0.0
                total_trips = vehicle_data.get('total_trips', 0) or vehicle_data.get('trip_count', 0) or 0
                
                top_vehicles.append({
                    'vehicle_id': vehicle_id,
                    'vehicle_name': vehicle_data.get('name', 'Unknown Vehicle'),
                    'revenue': round(revenue, 2),
                    'utilization': round(utilization, 1),
                    'rating': round(float(rating), 1),
                    'trips': int(total_trips)
                })
        
        # Sort by revenue descending and take top N
        top_vehicles.sort(key=lambda x: x['revenue'], reverse=True)
        top_vehicles = top_vehicles[:limit]
        
        # Add rank
        for idx, vehicle in enumerate(top_vehicles, 1):
            vehicle['rank'] = idx
        
        return top_vehicles
    
# ------------------------------ END OF FILE ------------------------------

