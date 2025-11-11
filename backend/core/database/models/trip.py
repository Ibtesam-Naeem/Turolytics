# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ TRIP MODEL ------------------------------

class Trip(Base):
    """Trip model - represents a Turo trip/reservation with all related data."""
    
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    
    trip_id = Column(String, nullable=False, index=True, comment="Turo trip ID")
    trip_url = Column(String, nullable=True, comment="Trip URL on Turo")
    
    customer_name = Column(String, nullable=True, comment="Customer name")
    status = Column(String, nullable=False, index=True, comment="Trip status (COMPLETED, CANCELLED, etc.)")
    trip_type = Column(String, nullable=True, comment="Trip type (booked_trips or trip_history)")
    
    cancellation_info = Column(String, nullable=True, comment="Cancellation information")
    cancelled_by = Column(String, nullable=True, comment="Who cancelled the trip")
    cancelled_date = Column(String, nullable=True, comment="Cancellation date")
    
    start_date = Column(String, nullable=True, comment="Start date (e.g., 'Sat, Nov 1')")
    start_time = Column(String, nullable=True, comment="Start time (e.g., '4:30 p.m.')")
    end_date = Column(String, nullable=True, comment="End date (e.g., 'Fri, Nov 7')")
    end_time = Column(String, nullable=True, comment="End time (e.g., '5:30 a.m.')")
    
    location_type = Column(String, nullable=True, comment="Location type (Delivery, Location)")
    address = Column(String, nullable=True, comment="Full address")
    
    kilometers_included = Column(Integer, nullable=True, comment="Kilometers included in trip")
    kilometers_driven = Column(Integer, nullable=True, comment="Kilometers actually driven")
    overage_rate = Column(Float, nullable=True, comment="Overage rate per kilometer")
    
    total_earnings = Column(Float, nullable=True, comment="Total earnings amount")
    
    protection_plan = Column(String, nullable=True, comment="Protection plan name (e.g., '75 plan')")
    deductible = Column(String, nullable=True, comment="Deductible amount (e.g., '$0')")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    
    @property
    def receipt_url(self) -> str:
        """Generate receipt URL dynamically from trip_id."""
        if self.trip_id:
            return f"https://turo.com/ca/en/reservation/{self.trip_id}/receipt"
        return None
    
    @property
    def reservation_number(self) -> str:
        """Reservation number is the same as trip_id."""
        return self.trip_id
    
    @property
    def trip_dates(self) -> str:
        """Generate trip dates string from start_date and end_date."""
        if self.start_date and self.end_date:
            start = self.start_date.split(', ')[-1] if ', ' in self.start_date else self.start_date
            end = self.end_date.split(', ')[-1] if ', ' in self.end_date else self.end_date
            return f"{start} - {end}"
        return None
    
    def __repr__(self):
        return f"<Trip(id={self.id}, trip_id={self.trip_id}, status={self.status})>"
