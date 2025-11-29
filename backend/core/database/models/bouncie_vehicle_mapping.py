# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ BOUNCIE VEHICLE MAPPING MODEL ------------------------------

class BouncieVehicleMapping(Base):
    """
    Maps Turo vehicles to Bouncie IMEIs.
    Links a Turo vehicle to a Bouncie device.
    """
    
    __tablename__ = "bouncie_vehicle_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=False, index=True)
    
    # Bouncie device info
    imei = Column(String, nullable=False, index=True, comment="Bouncie device IMEI")
    bouncie_nickname = Column(String, nullable=True, comment="Bouncie vehicle nickname")
    bouncie_vin = Column(String, nullable=True, comment="Bouncie VIN")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="bouncie_vehicle_mappings")
    vehicle = relationship("Vehicle", back_populates="bouncie_mapping")
    
    def __repr__(self):
        return f"<BouncieVehicleMapping(id={self.id}, vehicle_id={self.vehicle_id}, imei={self.imei})>"

