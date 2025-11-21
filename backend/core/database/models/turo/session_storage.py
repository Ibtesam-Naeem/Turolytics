# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from core.database.connection import Base

# ------------------------------ SESSION STORAGE MODEL ------------------------------

class SessionStorage(Base):
    """Session storage model - stores browser session state for Turo login."""
    
    __tablename__ = "session_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    
    storage_state = Column(Text, nullable=True, comment="JSON string of browser storage state")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="Session expiration timestamp")
    
    account = relationship("Account", back_populates="session_storage")
    
    def __repr__(self):
        return f"<SessionStorage(id={self.id}, account_id={self.account_id})>"

