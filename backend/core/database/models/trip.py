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
    reservation_number = Column(String, nullable=True, index=True, comment="Reservation number")
    trip_url = Column(String, nullable=True, comment="Trip URL on Turo")
    
    customer_name = Column(String, nullable=True, comment="Customer name")
    status = Column(String, nullable=False, index=True, comment="Trip status (COMPLETED, CANCELLED, etc.)")
    trip_type = Column(String, nullable=True, comment="Trip type (booked_trips or trip_history)")
    
    cancellation_info = Column(String, nullable=True, comment="Cancellation information")
    cancelled_by = Column(String, nullable=True, comment="Who cancelled the trip")
    cancelled_date = Column(String, nullable=True, comment="Cancellation date")
    
    trip_dates = Column(String, nullable=True, comment="Trip dates string (e.g., 'Nov 1 - Nov 7')")
    
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
    receipt_url = Column(String, nullable=True, comment="Receipt URL")
    
    protection_plan = Column(String, nullable=True, comment="Protection plan name (e.g., '75 plan')")
    deductible = Column(String, nullable=True, comment="Deductible amount (e.g., '$0')")
    
    card_index = Column(Integer, nullable=True, comment="Card index from scraping")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    
    def __repr__(self):
        return f"<Trip(id={self.id}, trip_id={self.trip_id}, status={self.status})>"
