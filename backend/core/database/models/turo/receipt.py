# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ RECEIPT MODEL ------------------------------

class Receipt(Base):
    """Receipt model - represents a Turo trip receipt with detailed cost and earnings breakdown."""
    
    __tablename__ = "turo_receipts"
    
    __table_args__ = (
        Index('idx_receipt_account', 'account_id'),
        Index('idx_receipt_reservation', 'reservation_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    reservation_id = Column(String, nullable=True, index=True, comment="Turo reservation ID")
    
    vehicle_name = Column(String, nullable=True, comment="Vehicle name (without year)")
    vehicle_year = Column(String, nullable=True, comment="Vehicle year")
    booked_date = Column(String, nullable=True, comment="Date when trip was booked")
    trip_start = Column(String, nullable=True, comment="Trip start date and time")
    trip_end = Column(String, nullable=True, comment="Trip end date and time")
    pickup_location = Column(String, nullable=True, comment="Pickup location")
    return_location = Column(String, nullable=True, comment="Return location")
    
    guest_name = Column(String, nullable=True, comment="Guest name")
    
    distance_included = Column(Integer, nullable=True, comment="Distance included in kilometers")
    overage_rate = Column(Float, nullable=True, comment="Overage rate per kilometer")
    
    trip_price = Column(Float, nullable=True, comment="Base trip price")
    delivery_fee = Column(Float, nullable=True, comment="Delivery fee")
    trip_total = Column(Float, nullable=True, comment="Total trip cost (trip price + delivery fee - discounts + extras)")
    
    turo_fees = Column(Float, nullable=True, comment="Turo platform fees")
    sales_tax = Column(Float, nullable=True, comment="Sales tax on Turo services")
    you_earned = Column(Float, nullable=True, comment="Final amount earned (trip_total - turo_fees - sales_tax)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="receipts")
    
    def __repr__(self):
        return f"<Receipt(id={self.id}, reservation_id={self.reservation_id})>"

# ------------------------------ END OF FILE ------------------------------