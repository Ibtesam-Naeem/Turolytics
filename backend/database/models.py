# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON, Numeric, func, Index, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

# ------------------------------ BASE CONFIGURATION ------------------------------
Base = declarative_base()


# ------------------------------ ENUMS ------------------------------

class TripStatus(Enum):
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"


class PayoutType(Enum):
    TRIP_EARNINGS = "Trip earnings"
    REIMBURSEMENTS = "Reimbursements"
    VEHICLE_EARNINGS = "Vehicle earnings"
    BONUS = "Bonus"
    REFUND = "Refund"


class VehicleStatus(Enum):
    LISTED = "Listed"
    SNOOZED = "Snoozed"
    UNAVAILABLE = "Unavailable"
    MAINTENANCE = "Maintenance"


# ------------------------------ BASE MODEL ------------------------------

class BaseModel(Base):
    """Base model with common fields for all tables."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """Auto-generate table name from class name."""
        return cls.__name__.lower() + 's'
    
    def to_dict(self, include_relationships: bool = False) -> dict[str, Any]:
        """Convert model instance to dictionary.
        
        Args:
            include_relationships: Whether to include relationship data.
        """
        data = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                rel_data = getattr(self, relationship.key)
                if rel_data is None:
                    data[relationship.key] = None
                elif hasattr(rel_data, '__iter__') and not isinstance(rel_data, (str, bytes)):
                    data[relationship.key] = [item.to_dict() if hasattr(item, 'to_dict') else str(item) for item in rel_data]
                elif hasattr(rel_data, 'to_dict'):
                    data[relationship.key] = rel_data.to_dict()
                else:
                    data[relationship.key] = str(rel_data)
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """Create model instance from dictionary."""
        return cls(**{col.name: data.get(col.name) for col in cls.__table__.columns})
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# ------------------------------ ACCOUNT MODEL ------------------------------

class Account(BaseModel):
    """Turo account model."""
    
    __tablename__ = "accounts"
    
    turo_email = Column(String(255), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    vehicles = relationship("Vehicle", back_populates="account", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="account", cascade="all, delete-orphan")
    payouts = relationship("Payout", back_populates="account", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="account", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, turo_email={self.turo_email})>"


# ------------------------------ VEHICLE MODEL ------------------------------

class Vehicle(BaseModel):
    """Vehicle model."""
    
    __tablename__ = "vehicles"
    __table_args__ = (
        Index('ix_vehicle_account_turo_id', 'account_id', 'turo_vehicle_id'),
        UniqueConstraint('account_id', 'turo_vehicle_id', name='uq_vehicle_account_turo_id'),
    )
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    turo_vehicle_id = Column(String(100), nullable=True, index=True)
    
    name = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    trim = Column(String(100), nullable=True)
    license_plate = Column(String(50), nullable=True)
    
    status = Column(SQLEnum(VehicleStatus), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    rating = Column(Float, nullable=True)
    trip_count = Column(Integer, default=0, nullable=False)
    last_trip_at = Column(DateTime(timezone=True), nullable=True)
    
    image_url = Column(String(500), nullable=True)
    image_alt = Column(String(255), nullable=True)
    
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    account = relationship("Account", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, turo_id={self.turo_vehicle_id})>"


# ------------------------------ TRIP MODEL ------------------------------

class Trip(BaseModel):
    """Trip model."""
    
    __tablename__ = "trips"
    __table_args__ = (
        Index('ix_trip_account_turo_id', 'account_id', 'turo_trip_id'),
        UniqueConstraint('account_id', 'turo_trip_id', name='uq_trip_account_turo_id'),
    )
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    
    turo_trip_id = Column(String(100), nullable=True, index=True)
    turo_trip_url = Column(String(500), nullable=True)
    
    trip_dates = Column(String(100), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    customer_name = Column(String(255), nullable=True)
    customer_id = Column(String(100), nullable=True)
    customer_info = Column(JSON, nullable=True)
    customer_found = Column(Boolean, default=False, nullable=False)
    
    status = Column(SQLEnum(TripStatus), nullable=True)
    cancellation_info = Column(Text, nullable=True)
    cancelled_by = Column(String(100), nullable=True)
    cancelled_date = Column(DateTime(timezone=True), nullable=True)
    
    price_total = Column(Float, nullable=True)
    earnings = Column(Float, nullable=True)
    
    vehicle_image = Column(String(500), nullable=True)
    customer_profile_image = Column(String(500), nullable=True)
    has_customer_photo = Column(Boolean, default=False, nullable=False)
    
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    account = relationship("Account", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    
    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, turo_id={self.turo_trip_id})>"

# ------------------------------ PAYOUT MODELS ------------------------------

class Payout(BaseModel):
    """Payout model."""
    
    __tablename__ = "payouts"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    turo_payout_id = Column(String(100), nullable=True, index=True)
    
    payout_at = Column(DateTime(timezone=True), nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    method = Column(String(100), nullable=True)
    reference = Column(String(255), nullable=True)
    
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    account = relationship("Account", back_populates="payouts")
    payout_items = relationship("PayoutItem", back_populates="payout", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Payout(id={self.id}, turo_id={self.turo_payout_id})>"

class PayoutItem(BaseModel):
    """Payout item model."""
    
    __tablename__ = "payout_items"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)
    
    type = Column(SQLEnum(PayoutType), nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    description = Column(Text, nullable=True)
    
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    
    account = relationship("Account")
    payout = relationship("Payout", back_populates="payout_items")
    trip = relationship("Trip")
    
    def __repr__(self) -> str:
        return f"<PayoutItem(id={self.id}, type={self.type})>"

# ------------------------------ REVIEW MODEL ------------------------------

class Review(BaseModel):
    """Review model."""
    
    __tablename__ = "reviews"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)
    
    turo_review_id = Column(String(100), nullable=True, index=True)
    
    customer_name = Column(String(255), nullable=True)
    customer_id = Column(String(100), nullable=True)
    customer_image_url = Column(String(500), nullable=True)
    customer_image_alt = Column(String(255), nullable=True)
    
    rating = Column(Float, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    vehicle_info = Column(String(255), nullable=True)
    review_text = Column(Text, nullable=True)
    
    areas_of_improvement = Column(JSON, nullable=True)
    
    host_response = Column(Text, nullable=True)
    has_host_response = Column(Boolean, default=False, nullable=False)
    
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    account = relationship("Account", back_populates="reviews")
    trip = relationship("Trip")
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, turo_id={self.turo_review_id})>"


# ------------------------------ SESSION MODEL ------------------------------

class Session(BaseModel):
    """Browser session storage for Turo authentication."""
    __tablename__ = "sessions"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    storage_state = Column(JSON, nullable=False)  # Playwright storage state
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    
    # Relationships
    account = relationship("Account", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("ix_sessions_account_active", "account_id", "is_active"),
        Index("ix_sessions_expires", "expires_at"),
        Index("ix_sessions_last_used", "last_used_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, account_id={self.account_id}, active={self.is_active})>"

# ------------------------------ EXPORTS ------------------------------
__all__ = [
    "Base",
    "BaseModel",
    "TripStatus",
    "PayoutType", 
    "VehicleStatus",
    "Account",
    "Vehicle",
    "Trip",
    "Payout",
    "PayoutItem",
    "Review",
    "Session"
]

# ------------------------------ END OF FILE ------------------------------