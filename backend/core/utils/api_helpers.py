# ------------------------------ IMPORTS ------------------------------
import hashlib
from fastapi import HTTPException

# ------------------------------ API HELPER FUNCTIONS ------------------------------

def validate_credentials(email: str, password: str) -> None:
    """Validate email and password are provided."""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

def get_account_id(email: str) -> int:
    """Generate account ID from email hash."""
    # Use hash of email to generate consistent account_id
    email_hash = int(hashlib.md5(email.encode()).hexdigest()[:8], 16)
    # Ensure positive integer
    return abs(email_hash) % (10 ** 9)

# ------------------------------ END OF FILE ------------------------------