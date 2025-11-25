# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
import enum
from core.database.connection import Base

# ------------------------------ ENUMS ------------------------------

class DocumentCategory(str, enum.Enum):
    """Document category enum."""
    GAS_RECEIPT = "gas_receipt"
    PARKING_TICKET = "parking_ticket"
    TOLL_BOOTH = "toll_booth"
    INSURANCE = "insurance"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    REGISTRATION = "registration"
    INSPECTION = "inspection"
    BUSINESS_EXPENSE = "business_expense"
    OTHER = "other"

# ------------------------------ DOCUMENT MODEL ------------------------------

class Document(Base):
    """Document model - represents uploaded documents/files stored in S3."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True, comment="Vehicle ID if linked to specific car, NULL for general")
    
    file_name = Column(String, nullable=False, comment="Original file name")
    file_type = Column(String, nullable=True, comment="File MIME type (e.g., 'image/jpeg', 'application/pdf')")
    file_size = Column(Integer, nullable=True, comment="File size in bytes")
    
    s3_key = Column(String, nullable=False, unique=True, index=True, comment="S3 object key/path")
    s3_bucket = Column(String, nullable=False, comment="S3 bucket name")
    
    category = Column(Enum(DocumentCategory), nullable=False, index=True, comment="Document category")
    description = Column(String, nullable=True, comment="Optional description/notes")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    account = relationship("Account", back_populates="documents")
    vehicle = relationship("Vehicle", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, file_name={self.file_name}, category={self.category}, vehicle_id={self.vehicle_id})>"

