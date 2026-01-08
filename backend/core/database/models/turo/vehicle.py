# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ VEHICLE MODEL ------------------------------

class Vehicle(Base):
    """Vehicle model - represents a Turo vehicle listing."""
    
    __tablename__ = "turo_vehicles"
    
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
    
    utilization = Column(Float, nullable=True, comment="Vehicle utilization percentage (0-100) for last 30 days")
    utilization_period = Column(String, nullable=True, default="30d", comment="Period for utilization calculation (e.g., '30d', '90d', 'all_time')")
    utilization_goal = Column(Float, nullable=True, comment="Target utilization percentage (0-100) for this vehicle")
    
    listed_on_turo_date = Column(DateTime(timezone=True), nullable=True, comment="Date when vehicle was first listed on Turo")
    removed_from_turo_date = Column(DateTime(timezone=True), nullable=True, comment="Date when vehicle was removed from Turo (null means still active)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="vehicle", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="vehicle", cascade="all, delete-orphan")
    bouncie_mapping = relationship("BouncieVehicleMapping", back_populates="vehicle", uselist=False, cascade="all, delete-orphan")
    bouncie_dtc_codes = relationship("BouncieDTCCode", back_populates="vehicle", cascade="all, delete-orphan")
    bouncie_webhook_logs = relationship("BouncieWebhookLog", back_populates="vehicle", cascade="all, delete-orphan")
    utilization_history = relationship("VehicleUtilizationHistory", back_populates="vehicle", cascade="all, delete-orphan")
    odometer_history = relationship("VehicleOdometerHistory", back_populates="vehicle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, name={self.name}, license_plate={self.license_plate})>"


# ------------------------------ VEHICLE UTILIZATION HISTORY MODEL ------------------------------

class VehicleUtilizationHistory(Base):
    """Vehicle utilization history model - monthly utilization snapshots for trend analysis."""
    
    __tablename__ = "turo_vehicle_utilization_history"
    
    __table_args__ = (
        UniqueConstraint('vehicle_id', 'year', 'month', name='uq_vehicle_utilization_monthly'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=False, index=True, comment="Foreign key to Vehicle table")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Month tracking for charts/graphs
    year = Column(Integer, nullable=False, index=True, comment="Year (e.g., 2025)")
    month = Column(Integer, nullable=False, index=True, comment="Month (1-12)")
    
    booked_days = Column(Integer, nullable=False, comment="Number of booked days in the period")
    total_days = Column(Integer, nullable=False, comment="Total days in the period")
    
    calculated_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="When this snapshot was taken")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    vehicle = relationship("Vehicle", back_populates="utilization_history")
    account = relationship("Account", back_populates="vehicle_utilization_history")
    
    @property
    def utilization(self) -> float:
        """Calculate utilization percentage from booked_days and total_days."""
        if self.total_days == 0:
            return 0.0
        utilization = (self.booked_days / self.total_days) * 100
        return min(100.0, max(0.0, utilization))
    
    def __repr__(self):
        return f"<VehicleUtilizationHistory(id={self.id}, vehicle_id={self.vehicle_id}, year={self.year}, month={self.month}, utilization={self.utilization:.1f}%, calculated_at={self.calculated_at})>"

