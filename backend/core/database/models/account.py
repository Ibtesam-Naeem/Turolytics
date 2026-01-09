# ------------------------------ IMPORTS ------------------------------
import hashlib
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ ACCOUNT MODEL ------------------------------

class Account(Base):
    """Account model - represents a user account. Shared across all integrations."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True, comment="Hash-based user ID generated from email")
    email = Column(String, unique=True, nullable=False, index=True, comment="User email address")
    password_hash = Column(String, nullable=True, comment="Hashed password for authentication")
    
    # Profile fields
    first_name = Column(String, nullable=True, comment="User's first name")
    last_name = Column(String, nullable=True, comment="User's last name")
    phone_number = Column(String, nullable=True, comment="User's phone number")
    country = Column(String, nullable=True, comment="User's country")
    state = Column(String, nullable=True, comment="User's state/province")
    
    # 2FA fields (with defaults for existing database)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String, nullable=True)
    two_factor_method = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Password reset
    password_reset_token = Column(String, nullable=True, comment="Token for password reset")
    password_reset_expires = Column(DateTime(timezone=True), nullable=True, comment="Password reset token expiration")
    password_changed_at = Column(DateTime(timezone=True), nullable=True, comment="Timestamp when password was last changed")
    
    # Email verification
    email_verification_token = Column(String, nullable=True, comment="Token for email verification")
    email_verification_expires = Column(DateTime(timezone=True), nullable=True, comment="Email verification token expiration")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    vehicles = relationship("Vehicle", back_populates="account", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="account", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="account", cascade="all, delete-orphan")
    earnings_breakdowns = relationship("EarningsBreakdown", back_populates="account", cascade="all, delete-orphan")
    vehicle_earnings = relationship("VehicleEarnings", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    vehicle_utilization_history = relationship("VehicleUtilizationHistory", back_populates="account", cascade="all, delete-orphan")
    vehicle_odometer_history = relationship("VehicleOdometerHistory", back_populates="account", cascade="all, delete-orphan")
    session_storage = relationship("SessionStorage", back_populates="account", uselist=False, cascade="all, delete-orphan")
    bouncie_integration = relationship("BouncieIntegration", back_populates="account", uselist=False, cascade="all, delete-orphan")
    turo_integration = relationship("TuroIntegration", back_populates="account", uselist=False, cascade="all, delete-orphan")
    bouncie_vehicle_mappings = relationship("BouncieVehicleMapping", back_populates="account", cascade="all, delete-orphan")
    bouncie_trip_matches = relationship("BouncieTripMatch", back_populates="account", cascade="all, delete-orphan")
    bouncie_dtc_codes = relationship("BouncieDTCCode", back_populates="account", cascade="all, delete-orphan")
    bouncie_webhook_logs = relationship("BouncieWebhookLog", back_populates="account", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="account", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="account", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="account", cascade="all, delete-orphan")
    
    @staticmethod
    def get_user_id(email: str) -> int:
        """Generate user ID from email hash using SHA-256."""
        email_hash = int(hashlib.sha256(email.encode()).hexdigest()[:8], 16)
        return abs(email_hash) % (10 ** 9)
    
    def __repr__(self):
        return f"<Account(id={self.id}, user_id={self.user_id}, email={self.email})>"

