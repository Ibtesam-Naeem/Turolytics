# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, func, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ VEHICLE ODOMETER HISTORY MODEL ------------------------------

class VehicleOdometerHistory(Base):
    """Vehicle odometer history model - daily snapshots of odometer readings for trend analysis."""
    
    __tablename__ = "vehicle_odometer_history"
    
    __table_args__ = (
        UniqueConstraint('vehicle_id', 'date', name='uq_vehicle_odometer_daily'),
        Index('idx_vehicle_date', 'vehicle_id', 'date'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=False, index=True, comment="Foreign key to Vehicle table")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    imei = Column(String(50), nullable=True, index=True, comment="Bouncie IMEI if available")
    
    # Odometer reading (in miles from Bouncie)
    odometer_miles = Column(Float, nullable=False, comment="Odometer reading in miles")
    
    # Date for this snapshot (date only, no time)
    date = Column(DateTime(timezone=False), nullable=False, index=True, comment="Date of the snapshot (YYYY-MM-DD)")
    
    # Metadata
    source = Column(String(50), nullable=True, default="bouncie", comment="Source of odometer reading (bouncie, manual, etc.)")
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="When this snapshot was recorded")
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="odometer_history")
    account = relationship("Account", back_populates="vehicle_odometer_history")
    
    def __repr__(self):
        return f"<VehicleOdometerHistory(id={self.id}, vehicle_id={self.vehicle_id}, date={self.date}, odometer={self.odometer_miles} miles)>"

