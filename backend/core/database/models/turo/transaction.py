# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ TRANSACTION MODEL ------------------------------

class Transaction(Base):
    """Transaction model - represents a Turo transaction (trip earnings, payments, refunds, etc.)."""
    
    __tablename__ = "turo_transactions"
    
    __table_args__ = (
        Index('idx_transaction_account_date', 'account_id', 'date'),
        Index('idx_transaction_reservation', 'reservation_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("turo_trips.id"), nullable=True, index=True, comment="Foreign key to Trip table (if transaction is linked to a trip)")
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=True, index=True, comment="Foreign key to Vehicle table")
    
    # Transaction type and details
    type = Column(String, nullable=False, index=True, comment="Transaction type (trip, payment, etc.)")
    trip_name = Column(String, nullable=True, comment="Trip name (e.g., 'John's trip')")
    vehicle_name = Column(String, nullable=True, comment="Vehicle name (e.g., 'Hyundai Elantra 2017')")
    payment_details = Column(String, nullable=True, comment="Payment details (e.g., '*******2842')")
    
    # Transaction identifiers
    reservation_id = Column(String, nullable=True, index=True, comment="Turo reservation ID")
    date = Column(String, nullable=True, index=True, comment="Transaction date (e.g., 'Aug 30, 2025')")
    year = Column(String, nullable=True, index=True, comment="Year for transaction")
    
    # Amounts
    earnings_amount = Column(String, nullable=True, comment="Earnings amount as string (e.g., 'CA$18.75')")
    earnings_amount_numeric = Column(Float, nullable=True, comment="Earnings amount as numeric")
    payment_amount = Column(String, nullable=True, comment="Payment amount as string (e.g., 'CA$205.49')")
    payment_amount_numeric = Column(Float, nullable=True, comment="Payment amount as numeric")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    trip = relationship("Trip", backref="transactions")
    vehicle = relationship("Vehicle", backref="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, reservation_id={self.reservation_id}, date={self.date})>"

# ------------------------------ END OF FILE ------------------------------
