# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, ARRAY, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ REVIEW MODEL ------------------------------

class Review(Base):
    """Review model - represents a customer review/rating."""
    
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    
    customer_name = Column(String, nullable=True, comment="Customer name")
    customer_id = Column(String, nullable=True, index=True, comment="Customer ID on Turo")
    
    rating = Column(Float, nullable=True, comment="Rating (1-5)")
    date = Column(DateTime(timezone=True), nullable=True, comment="Review date")
    vehicle_info = Column(String, nullable=True, comment="Vehicle info string from scraping")
    review_text = Column(Text, nullable=True, comment="Review text content")
    
    areas_of_improvement = Column(ARRAY(String), nullable=True, comment="List of areas of improvement")
    
    host_response = Column(Text, nullable=True, comment="Host response text")
    has_host_response = Column(Boolean, default=False, comment="Whether host has responded")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), nullable=True, comment="Last scraping timestamp")
    
    account = relationship("Account", back_populates="reviews")
    vehicle = relationship("Vehicle", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review(id={self.id}, customer_name={self.customer_name}, rating={self.rating})>"

