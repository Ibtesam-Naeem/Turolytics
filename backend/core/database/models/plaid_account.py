# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func, Enum
from sqlalchemy.orm import relationship
import enum
from core.database.connection import Base

# ------------------------------ ENUMS ------------------------------

class AccountType(str, enum.Enum):
    """Plaid account type enum."""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"
    OTHER = "other"

class AccountSubtype(str, enum.Enum):
    """Plaid account subtype enum."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit card"
    MONEY_MARKET = "money market"
    CD = "cd"
    OTHER = "other"

# ------------------------------ PLAID ACCOUNT MODEL ------------------------------

class PlaidAccount(Base):
    """
    Plaid Account model - represents a linked bank account from Plaid.
    """
    
    __tablename__ = "plaid_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    plaid_integration_id = Column(Integer, ForeignKey("plaid_integration.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    plaid_account_id = Column(String, nullable=False, unique=True, index=True, comment="Plaid account ID")
    
    name = Column(String, nullable=False, comment="Account name (e.g., 'Chase Checking')")
    official_name = Column(String, nullable=True, comment="Official account name from bank")
    type = Column(Enum(AccountType), nullable=False, comment="Account type")
    subtype = Column(Enum(AccountSubtype), nullable=True, comment="Account subtype")
    mask = Column(String, nullable=True, comment="Last 4 digits of account number")
    
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="Whether to monitor this account for transactions")
    
    balance_current = Column(String, nullable=True, comment="Current balance (as string to preserve precision)")
    balance_available = Column(String, nullable=True, comment="Available balance")
    balance_limit = Column(String, nullable=True, comment="Credit limit (for credit cards)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    plaid_integration = relationship("PlaidIntegration", back_populates="plaid_accounts")
    account = relationship("Account", back_populates="plaid_accounts")
    transactions = relationship("Transaction", back_populates="plaid_account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlaidAccount(id={self.id}, name={self.name}, plaid_account_id={self.plaid_account_id})>"

