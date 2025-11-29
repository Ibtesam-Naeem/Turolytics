# ------------------------------ IMPORTS ------------------------------
import hashlib
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ ACCOUNT MODEL ------------------------------

class Account(Base):
    """Account model - represents a user account. Shared across all integrations."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True, comment="Hash-based user ID generated from email")
    email = Column(String, unique=True, nullable=False, index=True, comment="User email address")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicles = relationship("Vehicle", back_populates="account", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="account", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="account", cascade="all, delete-orphan")
    earnings_breakdowns = relationship("EarningsBreakdown", back_populates="account", cascade="all, delete-orphan")
    vehicle_earnings = relationship("VehicleEarnings", back_populates="account", cascade="all, delete-orphan")
    session_storage = relationship("SessionStorage", back_populates="account", uselist=False, cascade="all, delete-orphan")
    bouncie_integration = relationship("BouncieIntegration", back_populates="account", uselist=False, cascade="all, delete-orphan")
    bouncie_vehicle_mappings = relationship("BouncieVehicleMapping", back_populates="account", cascade="all, delete-orphan")
    bouncie_trip_matches = relationship("BouncieTripMatch", back_populates="account", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="account", cascade="all, delete-orphan")
    
    @staticmethod
    def get_user_id(email: str) -> int:
        """Generate user ID from email hash using SHA-256."""
        email_hash = int(hashlib.sha256(email.encode()).hexdigest()[:8], 16)
        return abs(email_hash) % (10 ** 9)
    
    def __repr__(self):
        return f"<Account(id={self.id}, user_id={self.user_id}, email={self.email})>"

