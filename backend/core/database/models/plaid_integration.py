# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ PLAID INTEGRATION MODEL ------------------------------

class PlaidIntegration(Base):
    """
    Plaid Integration model - stores OAuth tokens and integration status for an account.
    """
    
    __tablename__ = "plaid_integration"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    
    access_token = Column(String, nullable=False, comment="Plaid access token")
    item_id = Column(String, nullable=False, unique=True, index=True, comment="Plaid item ID")
    
    institution_id = Column(String, nullable=True, comment="Plaid institution ID")
    institution_name = Column(String, nullable=True, comment="Bank/institution name")
    
    last_sync_at = Column(DateTime(timezone=True), nullable=True, comment="Last successful transaction sync")
    cursor = Column(String, nullable=True, comment="Plaid cursor for pagination")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="plaid_integration")
    plaid_accounts = relationship("PlaidAccount", back_populates="plaid_integration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlaidIntegration(id={self.id}, account_id={self.account_id}, institution_name={self.institution_name})>"

