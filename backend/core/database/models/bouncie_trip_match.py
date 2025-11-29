# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, func, JSON
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ BOUNCIE TRIP MATCH MODEL ------------------------------

class BouncieTripMatch(Base):
    """
    Stores matched trips between Turo and Bouncie.
    Links a Turo trip to one or more Bouncie trips.
    """
    
    __tablename__ = "bouncie_trip"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("turo_trips.id"), nullable=False, index=True)
    
    # Match metadata
    bouncie_trip_count = Column(Integer, nullable=False, comment="Number of Bouncie trips matched")
    aggregated_distance_km = Column(Float, nullable=True, comment="Total distance in km")
    aggregated_distance_miles = Column(Float, nullable=True, comment="Total distance in miles")
    total_duration_hours = Column(Float, nullable=True, comment="Total duration in hours")
    
    # GPS data (stored as JSON for flexibility)
    coordinates = Column(JSON, nullable=True, comment="All GPS coordinates as [[lat, lon], ...]")
    polyline = Column(Text, nullable=True, comment="Encoded polyline string for route")
    coordinate_count = Column(Integer, nullable=True, comment="Number of GPS points")
    
    # Time windows
    bouncie_earliest_start = Column(DateTime(timezone=True), nullable=True)
    bouncie_latest_end = Column(DateTime(timezone=True), nullable=True)
    
    # Raw match data (for debugging/reference)
    match_data = Column(JSON, nullable=True, comment="Full match result data")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="bouncie_trip_matches")
    trip = relationship("Trip", back_populates="bouncie_match")
    
    def __repr__(self):
        return f"<BouncieTripMatch(id={self.id}, trip_id={self.trip_id}, bouncie_trip_count={self.bouncie_trip_count})>"

