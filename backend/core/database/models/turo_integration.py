# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
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
    
    turo_email = Column(String(255), nullable=False)
    turo_password_encrypted = Column(String(500), nullable=False)
    
    has_active_session = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="turo_integration")
    
    def __repr__(self):
        return f"<TuroIntegration(id={self.id}, account_id={self.account_id}, email={self.turo_email})>"

# ------------------------------ END OF FILE ------------------------------