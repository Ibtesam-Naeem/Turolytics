# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import Column, Integer, DateTime, String, Text, func
from core.database.connection import Base

# ------------------------------ ACCOUNT DELETION LOG MODEL ------------------------------

class AccountDeletionLog(Base):
    """Audit log for account deletions. Stores minimal info (no PII) for compliance."""
    
    __tablename__ = "account_deletion_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True, comment="Deleted account ID (for reference)")
    user_id = Column(Integer, nullable=False, index=True, comment="Hash-based user ID (not PII)")
    deleted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deletion_reason = Column(Text, nullable=True, comment="User-provided reason for account deletion")
    ip_address = Column(String, nullable=True, comment="IP address at time of deletion (for security/fraud prevention)")
    
    def __repr__(self):
        return f"<AccountDeletionLog(id={self.id}, account_id={self.account_id}, user_id={self.user_id}, deleted_at={self.deleted_at})>"

