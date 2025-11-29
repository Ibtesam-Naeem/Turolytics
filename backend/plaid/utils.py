# ------------------------------ IMPORTS ------------------------------
from sqlalchemy.orm import Session
from core.database.models import Account
from core.database.db_service import DatabaseService
from fastapi import HTTPException

# ------------------------------ HELPER FUNCTIONS ------------------------------

def get_account_or_raise(db: Session, account_id: int) -> Account:
    """Get account by ID or user_id, raise HTTPException if not found."""
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        account = DatabaseService.get_account_by_user_id(db, account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return account

# ------------------------------ END OF FILE ------------------------------

