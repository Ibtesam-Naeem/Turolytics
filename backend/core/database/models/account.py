# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ ACCOUNT MODEL ------------------------------

class Account(Base):
    """Account model - represents a Turo account and scraping sessions."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, unique=True, nullable=False, index=True, comment="Turo account ID")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicles = relationship("Vehicle", back_populates="account", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="account", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="account", cascade="all, delete-orphan")
    earnings_breakdowns = relationship("EarningsBreakdown", back_populates="account", cascade="all, delete-orphan")
    vehicle_earnings = relationship("VehicleEarnings", back_populates="account", cascade="all, delete-orphan")
    session_storage = relationship("SessionStorage", back_populates="account", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, account_id={self.account_id})>"

