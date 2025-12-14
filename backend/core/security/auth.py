from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config.settings import settings
from core.database import get_db
from core.database.models import Account
from core.database.db_service import DatabaseService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.security.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)

def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    account = DatabaseService.get_account_by_user_id(db, user_id)
    if account is None:
        raise credentials_exception
    
    return account

async def get_current_active_user(
    current_user: Account = Depends(get_current_user)
) -> Account:
    return current_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[Account]:
    account = db.query(Account).filter(Account.email == email).first()
    if not account or not account.password_hash:
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account

def create_user(db: Session, email: str, password: str) -> Account:
    existing_account = db.query(Account).filter(Account.email == email).first()
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = Account.get_user_id(email)
    existing_user_id = DatabaseService.get_account_by_user_id(db, user_id)
    if existing_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email already exists"
        )
    
    account = Account(
        user_id=user_id,
        email=email,
        password_hash=get_password_hash(password)
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)

def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)

