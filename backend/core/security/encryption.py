# ------------------------------ IMPORTS ------------------------------
from cryptography.fernet import Fernet
import os
import base64
from typing import Optional

# ------------------------------ ENCRYPTION UTILITIES ------------------------------

def get_encryption_key() -> bytes:
    """Get or generate encryption key from environment variable."""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Generate a key if not set (for development only - should be set in production)
        key = Fernet.generate_key().decode()
        print(f"WARNING: ENCRYPTION_KEY not set. Generated key: {key}")
        print("Set this in your .env file for production use!")
    else:
        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode()
    return key

def encrypt_password(password: str) -> str:
    """Encrypt a password using Fernet symmetric encryption."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password using Fernet symmetric encryption."""
    key = get_encryption_key()
    f = Fernet(key)
    try:
        encrypted_bytes = base64.b64decode(encrypted_password.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt password: {str(e)}")

# ------------------------------ END OF FILE ------------------------------

