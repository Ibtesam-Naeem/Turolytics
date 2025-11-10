# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ EARNINGS BREAKDOWN MODEL ------------------------------

class EarningsBreakdown(Base):
    """Earnings breakdown model - breakdown of earnings by type."""
    
    __tablename__ = "earnings_breakdowns"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    type = Column(String, nullable=False, comment="Earnings type (Trip earnings, Upcoming earnings, etc.)")
    amount = Column(String, nullable=True, comment="Earnings amount as string (e.g., '$1,739')")
    amount_numeric = Column(Float, nullable=True, comment="Earnings amount as numeric")
    year = Column(String, nullable=True, comment="Year for earnings")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="earnings_breakdowns")
    
    def __repr__(self):
        return f"<EarningsBreakdown(id={self.id}, type={self.type}, amount={self.amount})>"


# ------------------------------ VEHICLE EARNINGS MODEL ------------------------------

class VehicleEarnings(Base):
    """Vehicle earnings model - earnings per vehicle."""
    
    __tablename__ = "vehicle_earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    vehicle_name = Column(String, nullable=False, comment="Vehicle name (e.g., 'Hyundai Elantra 2017')")
    license_plate = Column(String, nullable=True, index=True, comment="License plate number")
    trim = Column(String, nullable=True, comment="Vehicle trim level")
    
    earnings_amount = Column(String, nullable=True, comment="Earnings amount as string (e.g., '$1,738.78')")
    earnings_amount_numeric = Column(Float, nullable=True, comment="Earnings amount as numeric")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="vehicle_earnings")
    
    def __repr__(self):
        return f"<VehicleEarnings(id={self.id}, vehicle_name={self.vehicle_name}, earnings={self.earnings_amount})>"

