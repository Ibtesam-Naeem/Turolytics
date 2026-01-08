from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    user_id: int
    email: str
    email_verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    password_changed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    token: str

class ProfileUpdateRequest(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None

class AccountDeletionRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000, description="Reason for account deletion")

class UserSessionOut(BaseModel):
    id: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    last_used_at: datetime
    expires_at: Optional[datetime] = None
    is_active: int
    is_current: bool = False  # Whether this is the current session
    
    class Config:
        from_attributes = True