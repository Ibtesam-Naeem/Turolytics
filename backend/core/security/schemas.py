from pydantic import BaseModel, EmailStr
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

