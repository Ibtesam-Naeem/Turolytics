# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ BOUNCIE DTC CODE MODEL ------------------------------

class BouncieDTCCode(Base):
    """
    Bouncie Diagnostic Trouble Code (DTC) model.
    Stores engine codes received from Bouncie webhooks or API.
    """
    
    __tablename__ = "bouncie_dtc_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=True, index=True, comment="Linked Turo vehicle if mapped")
    
    # Bouncie device info
    imei = Column(String, nullable=False, index=True, comment="Bouncie device IMEI")
    
    # DTC Code information
    code = Column(String, nullable=False, index=True, comment="DTC code (e.g., 'P0301', 'P0420')")
    description = Column(Text, nullable=True, comment="Code description from Bouncie")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="Whether code is currently active")
    
    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="When the code first appeared")
    cleared_at = Column(DateTime(timezone=True), nullable=True, comment="When the code was cleared (if cleared)")
    
    # Metadata
    raw_data = Column(Text, nullable=True, comment="Raw webhook payload for debugging")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="bouncie_dtc_codes")
    vehicle = relationship("Vehicle", back_populates="bouncie_dtc_codes")
    
    def __repr__(self):
        return f"<BouncieDTCCode(id={self.id}, code={self.code}, imei={self.imei}, is_active={self.is_active})>"

