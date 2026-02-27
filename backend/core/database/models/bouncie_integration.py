# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ BOUNCIE INTEGRATION MODEL ------------------------------

class BouncieIntegration(Base):
    """
    Bouncie Integration model - stores OAuth tokens and integration status for an account.
    One account can have one Bouncie integration.
    """
    
    __tablename__ = "bouncie_token"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    bouncie_user_id = Column(String(100), nullable=True)
    bouncie_user_email = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="bouncie_integration")
    
    def __repr__(self):
        return f"<BouncieIntegration(id={self.id}, account_id={self.account_id})>"

# ------------------------------ END OF FILE ------------------------------