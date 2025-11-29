# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, func, JSON, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ TRANSACTION MODEL ------------------------------

class Transaction(Base):
    """
    Transaction model - represents a bank transaction from Plaid.
    Stores filtered and categorized vehicle-related transactions.
    """
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    plaid_account_id = Column(Integer, ForeignKey("plaid_accounts.id"), nullable=False, index=True)
    
    plaid_transaction_id = Column(String, nullable=False, unique=True, index=True, comment="Plaid transaction ID")
    
    date = Column(DateTime(timezone=True), nullable=False, index=True, comment="Transaction date")
    amount = Column(Numeric(10, 2), nullable=False, comment="Transaction amount (positive for income, negative for expenses)")
    merchant_name = Column(String, nullable=True, index=True, comment="Merchant name")
    name = Column(String, nullable=False, comment="Transaction name/description")
    
    category_primary = Column(String, nullable=True, index=True, comment="Primary category from Plaid")
    category_detailed = Column(String, nullable=True, comment="Detailed category from Plaid")
    plaid_category = Column(JSON, nullable=True, comment="Full Plaid category array")
    
    is_vehicle_related = Column(Boolean, default=False, nullable=False, index=True, comment="Whether transaction is vehicle-related")
    vehicle_category = Column(String, nullable=True, index=True, comment="Vehicle category (gas, insurance, repair, etc.)")
    transaction_type = Column(String, nullable=True, index=True, comment="Type: 'expense' or 'revenue'")
    
    match_confidence = Column(Numeric(3, 2), nullable=True, comment="Confidence score for vehicle-related classification (0.0-1.0)")
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True, comment="Linked receipt/document ID")
    
    plaid_data = Column(JSON, nullable=True, comment="Full Plaid transaction data")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="transactions")
    plaid_account = relationship("PlaidAccount", back_populates="transactions")
    document = relationship("Document", foreign_keys=[document_id])
    
    __table_args__ = (
        Index('idx_transactions_account_date', 'account_id', 'date'),
        Index('idx_transactions_vehicle_date', 'is_vehicle_related', 'date'),
        Index('idx_transactions_type_date', 'transaction_type', 'date'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, plaid_transaction_id={self.plaid_transaction_id}, amount={self.amount}, date={self.date})>"

