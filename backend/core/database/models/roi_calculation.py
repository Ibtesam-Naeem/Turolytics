# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ ROI CALCULATION MODEL ------------------------------

class ROICalculation(Base):
    """ROI Calculation model - stores saved ROI calculator calculations for users."""
    
    __tablename__ = "roi_calculations"
    
    __table_args__ = (
        Index('idx_roi_account', 'account_id'),
        Index('idx_roi_created', 'account_id', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True, comment="Foreign key to Account table")
    
    # Calculation fields
    vehicle_name = Column(String, nullable=False, comment="Vehicle name (e.g., '2024 Tesla Model 3')")
    vehicle_price = Column(Float, nullable=False, comment="Vehicle purchase price")
    daily_rate = Column(Float, nullable=False, comment="Daily rental rate")
    booking_days = Column(Integer, nullable=False, comment="Booking days per month")
    monthly_expenses = Column(Float, nullable=False, comment="Monthly maintenance & misc expenses")
    insurance_monthly = Column(Float, nullable=False, comment="Monthly insurance cost")
    annual_depreciation = Column(Float, nullable=False, comment="Annual depreciation amount")
    
    # Calculated results (stored for reference)
    roi = Column(Float, nullable=False, comment="Calculated ROI percentage")
    annual_profit = Column(Float, nullable=False, comment="Calculated annual profit")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="roi_calculations")
    
    def __repr__(self):
        return f"<ROICalculation(id={self.id}, vehicle_name={self.vehicle_name}, roi={self.roi}%)>"
