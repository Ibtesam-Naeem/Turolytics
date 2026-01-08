# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, func, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ USER SESSION MODEL ------------------------------

class UserSession(Base):
    """User session model - tracks active login sessions for users."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Session identifier (JWT token hash or session token)
    session_token_hash = Column(String(64), nullable=False, unique=True, index=True, comment="Hash of the session token")
    
    # Device and location info
    user_agent = Column(Text, nullable=True, comment="User agent string from browser")
    ip_address = Column(String(45), nullable=True, comment="IP address of the client")
    device_type = Column(String(50), nullable=True, comment="Device type (desktop, mobile, tablet)")
    browser = Column(String(50), nullable=True, comment="Browser name")
    os = Column(String(50), nullable=True, comment="Operating system")
    location = Column(String(100), nullable=True, comment="Location (city, country)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="Session expiration timestamp")
    
    # Status
    is_active = Column(Integer, default=1, nullable=False, comment="1 for active, 0 for revoked")
    
    # Relationships
    account = relationship("Account", back_populates="user_sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_account_active', 'account_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, account_id={self.account_id}, is_active={self.is_active})>"

