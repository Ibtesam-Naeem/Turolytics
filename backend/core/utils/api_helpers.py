# ------------------------------ IMPORTS ------------------------------
from fastapi import HTTPException
from core.db.operations.turo_operations import get_or_create_account

# ------------------------------ API HELPER FUNCTIONS ------------------------------

def validate_credentials(email: str, password: str) -> None:
    """Validate email and password are provided."""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

def get_account_id(email: str) -> int:
    """Get or create account and return account ID."""
    account_id = get_or_create_account(email)
    if not account_id:
        raise HTTPException(status_code=500, detail="Failed to create or retrieve account")
    return account_id

# ------------------------------ END OF FILE ------------------------------