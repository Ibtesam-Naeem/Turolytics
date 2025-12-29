# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, func, JSON
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ BOUNCIE WEBHOOK LOG MODEL ------------------------------

class BouncieWebhookLog(Base):
    """
    Bouncie webhook event log model.
    Stores all incoming webhook events for debugging, auditing, and monitoring.
    """
    
    __tablename__ = "bouncie_webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True, comment="Account ID if IMEI is mapped")
    vehicle_id = Column(Integer, ForeignKey("turo_vehicles.id"), nullable=True, index=True, comment="Vehicle ID if IMEI is mapped")
    
    # Webhook metadata
    event_type = Column(String, nullable=False, index=True, comment="Webhook event type (e.g., 'new_mil_event')")
    imei = Column(String, nullable=True, index=True, comment="Device IMEI")
    
    # Request details
    raw_payload = Column(JSON, nullable=False, comment="Raw webhook payload")
    headers = Column(JSON, nullable=True, comment="Request headers")
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False, index=True, comment="Whether webhook was successfully processed")
    error_message = Column(Text, nullable=True, comment="Error message if processing failed")
    
    # Signature verification
    signature_valid = Column(Boolean, nullable=True, comment="Whether webhook signature was valid")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    account = relationship("Account", back_populates="bouncie_webhook_logs")
    vehicle = relationship("Vehicle", back_populates="bouncie_webhook_logs")
    
    def __repr__(self):
        return f"<BouncieWebhookLog(id={self.id}, event_type={self.event_type}, imei={self.imei}, processed={self.processed})>"

