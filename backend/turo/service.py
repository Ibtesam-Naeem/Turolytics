# ------------------------------ IMPORTS ------------------------------
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, func, text
from datetime import datetime, timezone, timedelta, date
from calendar import monthrange
import re

from core.database.models import Trip, Vehicle, Review, EarningsBreakdown, VehicleEarnings, Account
from . import parsing

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
        
        breakdowns = breakdown_query.all()
        vehicle_earnings = vehicle_earnings_query.all()
        
        return breakdowns, vehicle_earnings
    
    def _is_date_today(self, date_str: Optional[str]) -> bool:
        """Check if a date string represents today."""
        if not date_str:
            return False
        
        parsed_date = parsing._parse_turo_date(date_str)
        if not parsed_date:
            return False
        
        today = datetime.now(timezone.utc).date()
        # Make parsed_date timezone-aware if needed
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date.date() == today
    
    def _calculate_vehicle_utilization(
        self,
        vehicle_id: int,
        account: Account,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> float:
        """
        Calculate vehicle utilization for a given period based on actual trip dates.
        
        Utilization = (unique booked days / total days in period) * 100
        
        Args:
            vehicle_id: Vehicle ID to calculate utilization for
            account: Account object
            period_start: Start of period (defaults to vehicle creation date or 30 days ago)
            period_end: End of period (defaults to today)
        
        Returns:
            Utilization percentage (0-100)
        """
        # Default period: last 30 days or since vehicle creation
        if period_end is None:
            period_end = datetime.now(timezone.utc)
        
        # Get vehicle to determine creation date
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.account_id == account.id
        ).first()
        
        if not vehicle:
            return 0.0
        
        # Default period_start to vehicle creation or 30 days ago
        if period_start is None:
            if vehicle.created_at:
                period_start = vehicle.created_at
                # Ensure timezone-aware
                if period_start.tzinfo is None:
                    period_start = period_start.replace(tzinfo=timezone.utc)
            else:
                period_start = period_end - timedelta(days=30)
        
        # Get all trips for this vehicle (excluding cancelled)
        trips = self.db.query(Trip).filter(
            Trip.vehicle_id == vehicle_id,
            Trip.account_id == account.id,
            ~Trip.status.in_(['CANCELLED', 'CANCELED'])
        ).all()
        
        if not trips:
            return 0.0
        
        # Build set of unique booked dates
        booked_dates = set()
        period_start_date = period_start.date()
        period_end_date = period_end.date()
        
        for trip in trips:
            # Parse start and end dates
            start_date_obj = None
            end_date_obj = None
            
            if trip.start_date:
                start_date_obj = parsing._parse_turo_date(trip.start_date)
                if start_date_obj:
                    # Use scraped_at year if available for better accuracy
                    if trip.scraped_at:
                        try:
                            scraped_year = trip.scraped_at.year
                            start_date_obj = parsing._parse_turo_date(trip.start_date, scraped_year)
                        except:
                            pass
                    if start_date_obj and start_date_obj.tzinfo is None:
                        start_date_obj = start_date_obj.replace(tzinfo=timezone.utc)
            
            if trip.end_date:
                end_date_obj = parsing._parse_turo_date(trip.end_date)
                if end_date_obj:
                    # Use scraped_at year if available
                    if trip.scraped_at:
                        try:
                            scraped_year = trip.scraped_at.year
                            end_date_obj = parsing._parse_turo_date(trip.end_date, scraped_year)
                        except:
                            pass
                    if end_date_obj and end_date_obj.tzinfo is None:
                        end_date_obj = end_date_obj.replace(tzinfo=timezone.utc)
            
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
            return 0.0
        
        booked_days = len(booked_dates)
        utilization = (booked_days / total_days) * 100
        
        # Clamp between 0 and 100
        return min(100.0, max(0.0, utilization))
    
    def get_monthly_utilization(
        self,
        account: Account,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly utilization data for all vehicles.
        Returns utilization per month with vehicle breakdown.
        
        Args:
            account: Account object
            year: Year to get data for (defaults to current year)
        
        Returns:
            List of month data with utilization and vehicle breakdown
        """
        from calendar import monthrange
        
        if year is None:
            year = datetime.now(timezone.utc).year
        
        # Get all vehicles for the account
        vehicles = self.db.query(Vehicle).filter(
            Vehicle.account_id == account.id
        ).all()
        
        if not vehicles:
            return []
        
        # Get all trips for the account (excluding cancelled)
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            ~Trip.status.in_(['CANCELLED', 'CANCELED'])
        ).all()
        
        # Group trips by month
        monthly_data = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in range(1, 13):
            month_key = month_names[month - 1]
            month_start = datetime(year, month, 1, tzinfo=timezone.utc)
            _, last_day = monthrange(year, month)
            month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            
            # Calculate utilization for each vehicle in this month
            vehicle_utilizations = []
            total_days = last_day
            fleet_total_booked_days = 0
            
            for vehicle in vehicles:
                # Get trips for this vehicle in this month
                vehicle_trips = [
                    t for t in trips 
                    if t.vehicle_id == vehicle.id
                ]
                
                # Build set of booked dates for this vehicle in this month
                booked_dates = set()
                for trip in vehicle_trips:
                    start_date_obj = None
                    end_date_obj = None
                    
                    if trip.start_date:
                        start_date_obj = parsing._parse_turo_date(trip.start_date, year)
                        if start_date_obj and start_date_obj.tzinfo is None:
                            start_date_obj = start_date_obj.replace(tzinfo=timezone.utc)
                    
                    if trip.end_date:
                        end_date_obj = parsing._parse_turo_date(trip.end_date, year)
                        if end_date_obj and end_date_obj.tzinfo is None:
                            end_date_obj = end_date_obj.replace(tzinfo=timezone.utc)
                    
                    if start_date_obj and end_date_obj:
                        start_date = start_date_obj.date()
                        end_date = end_date_obj.date()
                        
                        # Only count dates within this month
                        month_start_date = month_start.date()
                        month_end_date = month_end.date()
                        
                        current = max(start_date, month_start_date)
                        end_date_clamped = min(end_date, month_end_date)
                        
                        while current <= end_date_clamped:
                            booked_dates.add(current)
                            current += timedelta(days=1)
                    elif start_date_obj:
                        start_date = start_date_obj.date()
                        month_start_date = month_start.date()
                        month_end_date = month_end.date()
                        if month_start_date <= start_date <= month_end_date:
                            booked_dates.add(start_date)
                
                booked_days = len(booked_dates)
                vehicle_utilization = (booked_days / total_days * 100) if total_days > 0 else 0.0
                vehicle_utilization = min(100.0, max(0.0, vehicle_utilization))
                
                # Count trips for this vehicle in this month
                vehicle_trip_count = len([
                    t for t in vehicle_trips
                    if (t.start_date and parsing._parse_turo_date(t.start_date, year) and
                        month_start <= parsing._parse_turo_date(t.start_date, year).replace(tzinfo=timezone.utc) <= month_end)
                ])
                
                if booked_days > 0 or vehicle_utilization > 0:
                    vehicle_utilizations.append({
                        'vehicle': vehicle.name,
                        'utilization': round(vehicle_utilization, 1),
                        'trips': vehicle_trip_count,
                        'daysRented': booked_days,
                        'totalDays': total_days,
                    })
                    fleet_total_booked_days += booked_days
            
            # Calculate fleet average utilization (average of all vehicle utilizations)
            if vehicle_utilizations:
                fleet_utilization = sum(v['utilization'] for v in vehicle_utilizations) / len(vehicle_utilizations)
            else:
                fleet_utilization = 0.0
            fleet_utilization = min(100.0, max(0.0, fleet_utilization))
            
            # Always include all months, even if utilization is 0
            monthly_data[month_key] = {
                'month': month_key,
                'utilization': round(fleet_utilization, 1),
                'vehicles': vehicle_utilizations,
            }
        
        # Return as list ordered by month, including all 12 months
        result = []
        for month in month_names:
            result.append(monthly_data[month])
        
        return result
    
    def get_monthly_utilization_v2(
        self,
        account: Account,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate monthly vehicle utilization using corrected business logic.
        
        Business logic:
        - Only COMPLETED trips
        - Multi-day trips: start_date to end_date - 1 day (inclusive start, exclusive end)
        - Same-day trips (start_date = end_date) count as 1 day
        - Trips spanning months are split correctly across months
        - Group by vehicle_id and month
        
        Args:
            account: Account object
            year: Year to get data for (defaults to current year)
        
        Returns:
            List of month data with utilization per vehicle and fleet average
        """
        if year is None:
            year = datetime.now(timezone.utc).year
        
        # Get all COMPLETED trips for this account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.status == 'COMPLETED',
            Trip.start_date.isnot(None),
            Trip.end_date.isnot(None)
        ).all()
        
        # Get all vehicles for this account
        vehicles = self.db.query(Vehicle).filter(
            Vehicle.account_id == account.id
        ).all()
        
        if not vehicles:
            return []
        
        vehicle_map = {v.id: v.name for v in vehicles}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Structure: {month_key: {vehicle_id: booked_days}}
        monthly_vehicle_days = {month: {} for month in month_names}
        
        # Process each trip
        for trip in trips:
            if not trip.vehicle_id:
                continue
                
            # Parse dates
            start_date_obj = None
            end_date_obj = None
            
            if trip.start_date:
                start_date_obj = parsing._parse_turo_date(trip.start_date, year)
                if start_date_obj and start_date_obj.tzinfo is None:
                    start_date_obj = start_date_obj.replace(tzinfo=timezone.utc)
            
            if trip.end_date:
                end_date_obj = parsing._parse_turo_date(trip.end_date, year)
                if end_date_obj and end_date_obj.tzinfo is None:
                    end_date_obj = end_date_obj.replace(tzinfo=timezone.utc)
            
            if not start_date_obj or not end_date_obj:
                continue
            
            start_date = start_date_obj.date()
            end_date = end_date_obj.date()
            
            # Business logic: Multi-day trips count from start_date to end_date - 1 day
            # Same-day trips count as 1 day
            if start_date == end_date:
                # Same-day trip: count as 1 day
                booked_dates = [start_date]
            else:
                # Multi-day trip: start_date to end_date - 1 day (inclusive)
                booked_dates = []
                current = start_date
                while current < end_date:  # Exclusive end_date
                    booked_dates.append(current)
                    current += timedelta(days=1)
            
            # Group booked dates by month
            for booked_date in booked_dates:
                if booked_date.year != year:
                    continue
                    
                month_num = booked_date.month
                month_key = month_names[month_num - 1]
                
                if trip.vehicle_id not in monthly_vehicle_days[month_key]:
                    monthly_vehicle_days[month_key][trip.vehicle_id] = 0
                
                monthly_vehicle_days[month_key][trip.vehicle_id] += 1
        
        # Build result with utilization calculations
        result = []
        for month_num in range(1, 13):
            month_key = month_names[month_num - 1]
            _, days_in_month = monthrange(year, month_num)
            
            vehicle_utilizations = []
            total_fleet_booked_days = 0
            
            # Calculate utilization for each vehicle
            for vehicle in vehicles:
                booked_days = monthly_vehicle_days[month_key].get(vehicle.id, 0)
                total_fleet_booked_days += booked_days
                
                utilization_percent = (booked_days / days_in_month * 100) if days_in_month > 0 else 0.0
                utilization_percent = round(utilization_percent, 2)
                
                # Get trip count for this vehicle in this month
                vehicle_trip_count = len([
                    t for t in trips
                    if t.vehicle_id == vehicle.id and
                    t.start_date and
                    parsing._parse_turo_date(t.start_date, year) and
                    parsing._parse_turo_date(t.start_date, year).date().month == month_num
                ])
                
                if booked_days > 0 or vehicle_trip_count > 0:
                    vehicle_utilizations.append({
                        'vehicle': vehicle.name,
                        'utilization': utilization_percent,
                        'trips': vehicle_trip_count,
                        'daysRented': booked_days,
                        'totalDays': days_in_month,
                    })
            
            # Calculate fleet average utilization
            # If only one vehicle has trips, use that vehicle's utilization directly
            # Otherwise, calculate as: (total booked days) / (days in month * number of vehicles) * 100
            total_vehicles = len(vehicles)
            vehicles_with_data = len(vehicle_utilizations)
            
            if vehicles_with_data == 1 and total_vehicles == 1:
                # Single vehicle: fleet utilization = vehicle utilization (exact match)
                fleet_utilization = vehicle_utilizations[0]['utilization']
            elif total_vehicles > 0 and days_in_month > 0:
                # Multiple vehicles: calculate fleet average
                fleet_utilization = (total_fleet_booked_days / (days_in_month * total_vehicles)) * 100
            else:
                fleet_utilization = 0.0
            
            fleet_utilization = round(fleet_utilization, 2)
            fleet_utilization = min(100.0, max(0.0, fleet_utilization))
            
            result.append({
                'month': month_key,
                'utilization': fleet_utilization,
                'vehicles': vehicle_utilizations,
            })
        
        return result
    
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
        
        # Get all trips for the account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id
        ).all()
        
        trips_today = []
        for trip in trips:
            # Skip completed or cancelled trips
            status_upper = (trip.status or '').upper()
            if any(s in status_upper for s in ['COMPLETED', 'CANCELLED', 'CANCELED']):
                continue
            
            # Check if trip is scheduled for today (start_date is today)
            is_scheduled_today = False
            if trip.start_date and self._is_date_today(trip.start_date):
                is_scheduled_today = True
            
            if is_scheduled_today:
                # Get vehicle name
                vehicle_name = "Unknown Vehicle"
                if trip.vehicle_id:
                    vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                    if vehicle:
                        vehicle_name = vehicle.name
                
                trips_today.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': vehicle_name,
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'location': trip.address or trip.location_type or 'Unknown Location',
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
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        
        # Get upcoming trips that were scraped today
        # Since we only scrape new trips, trips scraped today = new bookings today
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id,
            func.date(Trip.scraped_at) == today,
            Trip.trip_type == 'booked_trips'  # Only upcoming/booked trips
        ).all()
        
        new_bookings = []
        for trip in trips:
            # Filter out completed/cancelled trips to be safe
            status_upper = (trip.status or '').upper()
            if any(s in status_upper for s in ['COMPLETED', 'CANCELLED', 'CANCELED']):
                continue
            # Get vehicle name
            vehicle_name = "Unknown Vehicle"
            if trip.vehicle_id:
                vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                if vehicle:
                    vehicle_name = vehicle.name
            
            # Parse dates for display
            dates_str = "TBD"
            if trip.start_date and trip.end_date:
                dates_str = f"{trip.start_date} - {trip.end_date}"
            elif trip.start_date:
                dates_str = trip.start_date
            
            # Get earnings if available
            earnings_str = "$0"
            if trip.total_earnings:
                earnings_str = f"${trip.total_earnings:,.0f}"
            
            new_bookings.append({
                'id': trip.id,
                'trip_id': trip.trip_id,
                'guest_name': trip.customer_name or 'Unknown Guest',
                'vehicle_name': vehicle_name,
                'dates': dates_str,
                'amount': earnings_str,
                'created_at': trip.scraped_at.isoformat() if trip.scraped_at else None,
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
        # Get all trips for the account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id
        ).all()
        
        checkouts_today = []
        for trip in trips:
            # Check if end_date is today
            if trip.end_date and self._is_date_today(trip.end_date):
                # Get vehicle name
                vehicle_name = "Unknown Vehicle"
                if trip.vehicle_id:
                    vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                    if vehicle:
                        vehicle_name = vehicle.name
                
                checkouts_today.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': vehicle_name,
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'time': trip.end_time or 'TBD',
                    'location': trip.address or trip.location_type or 'Unknown Location',
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
        
        # Get all trips for the account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id
        ).all()
        
        upcoming_trips = []
        for trip in trips:
            # Skip completed or cancelled trips
            status_upper = (trip.status or '').upper()
            if any(s in status_upper for s in ['COMPLETED', 'CANCELLED', 'CANCELED']):
                continue
            
            # Check if start_date is in the future
            is_upcoming = False
            if trip.start_date:
                parsed_start = parsing._parse_turo_date(trip.start_date)
                if parsed_start:
                    # Make timezone-aware if needed
                    if parsed_start.tzinfo is None:
                        parsed_start = parsed_start.replace(tzinfo=timezone.utc)
                    # Check if start date is today or in the future
                    if parsed_start.date() >= today:
                        is_upcoming = True
                else:
                    # If we can't parse the date, check trip_type
                    # booked_trips are typically upcoming
                    trip_type = (trip.trip_type or '').lower()
                    if 'booked' in trip_type:
                        is_upcoming = True
            else:
                # If no start_date, check trip_type
                trip_type = (trip.trip_type or '').lower()
                if 'booked' in trip_type:
                    is_upcoming = True
            
            if is_upcoming:
                # Get vehicle name
                vehicle_name = "Unknown Vehicle"
                if trip.vehicle_id:
                    vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                    if vehicle:
                        vehicle_name = vehicle.name
                
                # Format start date for display
                start_date_display = trip.start_date or "TBD"
                if trip.start_time:
                    start_date_display = f"{start_date_display}, {trip.start_time}"
                
                # Get locations
                pickup_location = trip.address or trip.location_type or "Location TBD"
                dropoff_location = trip.address or trip.location_type or "Location TBD"  # Turo may not always provide separate dropoff
                
                # Calculate earnings
                earnings = trip.total_earnings or 0
                
                # Get kilometers allowed
                kms_allowed = trip.kilometers_included or 0
                
                upcoming_trips.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': vehicle_name,
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'pickup_location': pickup_location,
                    'dropoff_location': dropoff_location,
                    'earnings': earnings,
                    'kms_allowed': kms_allowed,
                    'start_date': start_date_display,
                    'start_date_raw': trip.start_date,
                    'start_time': trip.start_time,
                    'end_date': trip.end_date,
                    'end_time': trip.end_time,
                    'status': trip.status,
                })
        
        # Sort by start date (earliest first)
        upcoming_trips.sort(key=lambda x: (
            parsing._parse_turo_date(x.get('start_date_raw', '')) or datetime.max.replace(tzinfo=timezone.utc)
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
        
        # Get all trips for the account
        trips = self.db.query(Trip).filter(
            Trip.account_id == account.id
        ).all()
        
        current_trips = []
        for trip in trips:
            # Skip completed or cancelled trips
            status_upper = (trip.status or '').upper()
            if any(s in status_upper for s in ['COMPLETED', 'CANCELLED', 'CANCELED']):
                continue
            
            # Check if trip is currently active
            is_current = False
            
            # Check start_date - should be today or in the past
            start_date_valid = False
            if trip.start_date:
                parsed_start = parsing._parse_turo_date(trip.start_date)
                if parsed_start:
                    if parsed_start.tzinfo is None:
                        parsed_start = parsed_start.replace(tzinfo=timezone.utc)
                    if parsed_start.date() <= today:
                        start_date_valid = True
                else:
                    # If we can't parse, assume it's valid if trip_type is booked_trips
                    trip_type = (trip.trip_type or '').lower()
                    if 'booked' in trip_type:
                        start_date_valid = True
            else:
                # If no start_date, check if trip was created recently (within last 7 days)
                # and is not completed
                if trip.created_at:
                    days_ago = (datetime.now(timezone.utc) - trip.created_at).days
                    if days_ago <= 7:
                        start_date_valid = True
            
            # Check end_date - should be today or in the future (or not set)
            end_date_valid = True
            if trip.end_date:
                parsed_end = parsing._parse_turo_date(trip.end_date)
                if parsed_end:
                    if parsed_end.tzinfo is None:
                        parsed_end = parsed_end.replace(tzinfo=timezone.utc)
                    # If end_date is in the past, trip is not current
                    if parsed_end.date() < today:
                        end_date_valid = False
            
            # Also check if trip_type indicates it's an active trip
            trip_type = (trip.trip_type or '').lower()
            if 'booked' in trip_type and start_date_valid:
                is_current = True
            elif start_date_valid and end_date_valid:
                is_current = True
            
            if is_current:
                # Get vehicle name and year
                vehicle_name = "Unknown Vehicle"
                vehicle_year = None
                if trip.vehicle_id:
                    vehicle = self.db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
                    if vehicle:
                        vehicle_name = vehicle.name
                        # Try to get year from vehicle model
                        if vehicle.year:
                            try:
                                vehicle_year = int(vehicle.year)
                            except (ValueError, TypeError):
                                # If year is not a valid integer, try to parse from name
                                year_match = re.search(r'\b(19|20)\d{2}\b', vehicle_name)
                                if year_match:
                                    vehicle_year = int(year_match.group())
                                else:
                                    vehicle_year = datetime.now().year
                        else:
                            # Try to parse year from name (e.g., "2024 Tesla Model 3")
                            year_match = re.search(r'\b(19|20)\d{2}\b', vehicle_name)
                            if year_match:
                                vehicle_year = int(year_match.group())
                            else:
                                vehicle_year = datetime.now().year
                
                if not vehicle_year:
                    vehicle_year = datetime.now().year
                
                # Get location
                location = trip.address or trip.location_type or "Location TBD"
                
                # Get earnings
                earnings = trip.total_earnings or 0
                
                # Get kilometers
                kms_driven = trip.kilometers_driven or 0
                kms_allowed = trip.kilometers_included or 0
                
                # Determine status based on trip data
                # For now, we'll use a simple heuristic
                status = "Active"
                if status_upper:
                    if any(s in status_upper for s in ['IN_PROGRESS', 'ACTIVE', 'ONGOING']):
                        status = "Moving"
                    elif any(s in status_upper for s in ['PARKED', 'STOPPED']):
                        status = "Parked"
                
                current_trips.append({
                    'id': trip.id,
                    'trip_id': trip.trip_id,
                    'vehicle_name': vehicle_name,
                    'vehicle_year': vehicle_year,
                    'guest_name': trip.customer_name or 'Unknown Guest',
                    'location': location,
                    'coordinates': "N/A",  # Not available from Turo directly
                    'fuel_percent': None,  # Would come from Bouncie integration
                    'speed': 0,  # Would come from Bouncie integration
                    'status': status,
                    'kms_driven': kms_driven,
                    'kms_allowed': kms_allowed,
                    'earnings': earnings,
                    'top_speed': 0,  # Would come from Bouncie integration
                    'start_date': trip.start_date,
                    'start_time': trip.start_time,
                    'end_date': trip.end_date,
                    'end_time': trip.end_time,
                })
        
        # Sort by start date (most recent first)
        current_trips.sort(key=lambda x: (
            parsing._parse_turo_date(x.get('start_date', '')) or datetime.min.replace(tzinfo=timezone.utc)
        ), reverse=True)
        
        return current_trips[:limit]
    
    def get_vehicles_with_stats(
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
            # Get trip statistics - count all trips, sum earnings and odometer from trips with data
            # For revenue, only count completed trips
            trips_query = self.db.query(
                func.count(Trip.id).label('total_trips'),
                func.sum(Trip.total_earnings).label('total_revenue'),
                func.sum(Trip.kilometers_driven).label('total_odometer')
            ).filter(
                Trip.account_id == account.id,
                Trip.vehicle_id == vehicle.id
            )
            
            # Revenue should only come from completed trips
            revenue_query = self.db.query(
                func.sum(Trip.total_earnings).label('total_revenue')
            ).filter(
                Trip.account_id == account.id,
                Trip.vehicle_id == vehicle.id,
                Trip.status == 'COMPLETED'
            )
            
            trip_stats = trips_query.first()
            revenue_stats = revenue_query.first()
            total_trips = trip_stats.total_trips or 0
            total_revenue = float(revenue_stats.total_revenue or 0) if revenue_stats else 0.0
            total_odometer = int(trip_stats.total_odometer or 0)
            
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
            
            # Calculate utilization using actual trip dates
            utilization = self._calculate_vehicle_utilization(
                vehicle_id=vehicle.id,
                account=account
            )
            
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
                'created_at': vehicle.created_at,
                'updated_at': vehicle.updated_at,
                'scraped_at': vehicle.scraped_at,
                'total_revenue': total_revenue,
                'total_odometer': total_odometer,
                'total_trips': total_trips,
                'avg_rating': final_rating,
                'review_count': review_count,
                'utilization': round(utilization, 1),
            }
            
            vehicles_with_stats.append(vehicle_dict)
        
        return vehicles_with_stats, total
    
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
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in range(1, 13):
            month_key = month_names[month - 1]
            month_start = datetime(year, month, 1, tzinfo=timezone.utc)
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            
            # Calculate revenue for this month from trips
            month_revenue = 0.0
            for trip in trips:
                # Check if trip end_date falls in this month
                if trip.end_date:
                    parsed_end = parsing._parse_turo_date(trip.end_date, year)
                    if parsed_end:
                        if parsed_end.tzinfo is None:
                            parsed_end = parsed_end.replace(tzinfo=timezone.utc)
                        if month_start <= parsed_end <= month_end:
                            month_revenue += float(trip.total_earnings or 0)
                # Also check start_date if end_date is not available
                elif trip.start_date:
                    parsed_start = parsing._parse_turo_date(trip.start_date, year)
                    if parsed_start:
                        if parsed_start.tzinfo is None:
                            parsed_start = parsed_start.replace(tzinfo=timezone.utc)
                        if month_start <= parsed_start <= month_end:
                            month_revenue += float(trip.total_earnings or 0)
            
            # Always include all months, even if revenue is 0
            monthly_data[month_key] = {
                'month': month_key,
                'revenue': round(month_revenue, 2),
            }
        
        # Return as list ordered by month, including all 12 months
        result = []
        for month in month_names:
            result.append(monthly_data[month])
        
        return result
    
    def get_top_performing_vehicles(
        self,
        account: Account,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top performing vehicles ranked by revenue.
        Returns list of vehicles with revenue, utilization, rating, and trip count.
        """
        # Get all vehicles with stats
        vehicles_data, _ = self.get_vehicles_with_stats(
            account=account,
            limit=1000,  # Get all vehicles to calculate rankings
            offset=0
        )
        
        # Calculate utilization for each vehicle
        # Utilization = (estimated days booked / total days since vehicle creation) * 100
        from datetime import datetime, timezone
        
        top_vehicles = []
        for vehicle_data in vehicles_data:
            vehicle_id = vehicle_data['id']
            
            # Get all trips for this vehicle
            trips = self.db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.vehicle_id == vehicle_id
            ).all()
            
            # Calculate days since vehicle creation
            vehicle_created = vehicle_data.get('created_at')
            if vehicle_created:
                if isinstance(vehicle_created, str):
                    try:
                        vehicle_created = datetime.fromisoformat(vehicle_created.replace('Z', '+00:00'))
                    except:
                        vehicle_created = datetime.now(timezone.utc)
                elif isinstance(vehicle_created, datetime):
                    pass  # Already a datetime
                else:
                    vehicle_created = datetime.now(timezone.utc)
                
                # Ensure timezone-aware
                if vehicle_created.tzinfo is None:
                    vehicle_created = vehicle_created.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                days_since_creation = (now - vehicle_created).days
            else:
                days_since_creation = 30  # Default to 30 days if no creation date
            
            # Calculate utilization using actual trip dates
            vehicle_id = vehicle_data.get('id')
            total_trips = vehicle_data.get('total_trips', 0) or vehicle_data.get('trip_count', 0) or 0
            
            if vehicle_id:
                utilization = self._calculate_vehicle_utilization(
                    vehicle_id=vehicle_id,
                    account=account
                )
            else:
                utilization = 0.0
            
            # Only include vehicles with revenue
            revenue = vehicle_data.get('total_revenue', 0) or 0
            if revenue > 0:
                rating = vehicle_data.get('avg_rating') or vehicle_data.get('rating')
                if rating is None:
                    rating = 0.0
                else:
                    rating = float(rating)
                
                top_vehicles.append({
                    'vehicle_id': vehicle_id,
                    'vehicle_name': vehicle_data.get('name', 'Unknown Vehicle'),
                    'revenue': round(revenue, 2),
                    'utilization': round(utilization, 1),
                    'rating': round(rating, 1),
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

