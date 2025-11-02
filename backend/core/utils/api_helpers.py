# ------------------------------ IMPORTS ------------------------------
from fastapi import HTTPException

# ------------------------------ API HELPER FUNCTIONS ------------------------------

def validate_credentials(email: str, password: str) -> None:
    """Validate email and password are provided."""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

def get_account_id(email: str) -> int:
    """Get or create account and return account ID."""
    # Database removed - return default account ID for now
    # TODO: Implement file-based account management if needed
    return 1

# ------------------------------ END OF FILE ------------------------------