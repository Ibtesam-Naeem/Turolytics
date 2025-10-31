# ------------------------------ IMPORTS ------------------------------
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, JSON, func, Index, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

# ------------------------------ BASE CONFIGURATION ------------------------------
Base = declarative_base()

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
    sessions = relationship("Session", back_populates="account", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="account", cascade="all, delete-orphan")
    vehicle_snapshots = relationship("VehicleSnapshot", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, turo_email={self.turo_email})>"

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
    
    account = relationship("Account", back_populates="sessions")
    
    __table_args__ = (
        Index("ix_sessions_account_active", "account_id", "is_active"),
        Index("ix_sessions_expires", "expires_at"),
        Index("ix_sessions_last_used", "last_used_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, account_id={self.account_id}, active={self.is_active})>"

# ------------------------------ VEHICLE MODEL ------------------------------

class Vehicle(BaseModel):
    """Turo vehicle model."""
    
    __tablename__ = "vehicles"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # Listed, Snoozed, etc.
    name = Column(String(255), nullable=True)  # Vehicle name/model
    year = Column(String(10), nullable=True)  # Vehicle year
    trim = Column(String(100), nullable=True)  # Vehicle trim level
    license_plate = Column(String(50), nullable=False)  # License plate number
    trip_info = Column(String(500), nullable=True)  # Trip information text
    rating = Column(Float, nullable=True)  # Vehicle rating
    trip_count = Column(Integer, nullable=True)  # Number of trips
    
    account = relationship("Account", back_populates="vehicles")
    
    __table_args__ = (
        UniqueConstraint("account_id", "license_plate", name="uq_vehicle_account_license"),
        Index("ix_vehicles_account_status", "account_id", "status"),
        Index("ix_vehicles_license_plate", "license_plate"),
    )
    
    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, account_id={self.account_id}, license_plate={self.license_plate})>"

# ------------------------------ VEHICLE SNAPSHOT MODEL ------------------------------

class VehicleSnapshot(BaseModel):
    """Vehicle snapshot model for tracking aggregate statistics per scraping session."""
    
    __tablename__ = "vehicle_snapshots"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    total_vehicles = Column(Integer, nullable=False)
    listed_vehicles = Column(Integer, nullable=False)
    snoozed_vehicles = Column(Integer, nullable=False)
    scraped_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    account = relationship("Account", back_populates="vehicle_snapshots")
    
    __table_args__ = (
        Index("ix_vehicle_snapshots_account_scraped", "account_id", "scraped_at"),
    )
    
    def __repr__(self) -> str:
        return f"<VehicleSnapshot(id={self.id}, account_id={self.account_id}, scraped_at={self.scraped_at})>"

# ------------------------------ EXPORTS ------------------------------
__all__ = [
    "Base",
    "BaseModel",
    "Account",
    "Session",
    "Vehicle",
    "VehicleSnapshot"
]

# ------------------------------ END OF FILE ------------------------------
