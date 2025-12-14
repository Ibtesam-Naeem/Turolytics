# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ TURO INTEGRATION MODEL ------------------------------

class TuroIntegration(Base):
    """
    Turo Integration model - stores encrypted Turo credentials for an account.
    One account can have one Turo integration.
    """
    
    __tablename__ = "turo_integration"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    
    # Encrypted Turo Credentials
    turo_email = Column(String, nullable=False)
    turo_password_encrypted = Column(String, nullable=False)  # Encrypted password
    
    # Session info
    has_active_session = Column(String, default=False, nullable=False)  # Boolean stored as string for compatibility
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="turo_integration")
    
    def __repr__(self):
        return f"<TuroIntegration(id={self.id}, account_id={self.account_id}, email={self.turo_email})>"

