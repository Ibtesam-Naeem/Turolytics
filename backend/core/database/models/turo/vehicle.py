# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ VEHICLE MODEL ------------------------------

class Vehicle(Base):
    """Vehicle model - represents a Turo vehicle listing."""
    
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False, comment="Vehicle name (e.g., 'Hyundai Elantra')")
    year = Column(String, nullable=True, comment="Vehicle year")
    trim = Column(String, nullable=True, comment="Vehicle trim level")
    license_plate = Column(String, nullable=True, index=True, comment="License plate number")
    
    status = Column(String, nullable=True, comment="Vehicle status (Listed, Snoozed, etc.)")
    trip_info = Column(String, nullable=True, comment="Trip information string")
    rating = Column(Float, nullable=True, comment="Vehicle rating")
    trip_count = Column(Integer, nullable=True, comment="Number of trips")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="vehicle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, name={self.name}, license_plate={self.license_plate})>"

