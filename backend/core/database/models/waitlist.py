# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, DateTime, Text, func, Index
from core.database.connection import Base

# ------------------------------ WAITLIST MODEL ------------------------------

class Waitlist(Base):
    """Waitlist model - stores email addresses and optional information of users who want early access."""
    
    __tablename__ = "waitlist"
    
    __table_args__ = (
        Index('idx_waitlist_email', 'email'),
        Index('idx_waitlist_created', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True, comment="Email address")
    
    # Optional fields
    vehicle_count = Column(String, nullable=True, comment="Fleet size range (e.g., '1-5', '6-10')")
    tracking_product = Column(String, nullable=True, comment="Tracking product used (e.g., 'bouncie', 'built-in', 'other')")
    tracking_product_other = Column(String, nullable=True, comment="Other tracking product specification")
    would_use = Column(String, nullable=True, comment="Likelihood of using the product (e.g., 'definitely', 'probably')")
    price_willing = Column(String, nullable=True, comment="Price range willing to pay (e.g., '1-10', '11-25')")
    feedback = Column(Text, nullable=True, comment="User feedback and suggestions")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    notified_at = Column(DateTime(timezone=True), nullable=True, index=True, comment="When launch email was sent")
    
    def __repr__(self):
        return f"<Waitlist(id={self.id}, email={self.email}, created_at={self.created_at})>"
