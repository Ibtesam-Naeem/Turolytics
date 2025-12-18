from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from core.database import get_db
from core.database.models import Account
from core.security.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_active_user,
    verify_password,
    get_password_hash,
    generate_reset_token,
    generate_verification_token
)
from core.security.schemas import (
    UserRegister, UserLogin, Token, UserOut,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    EmailVerificationRequest, EmailVerificationConfirm, ProfileUpdateRequest
)
from core.config.settings import settings

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    account = create_user(
        db, 
        user_data.email, 
        user_data.password,
        first_name=user_data.firstName,
        last_name=user_data.lastName,
        phone=user_data.phone,
        country=user_data.country,
        state=user_data.state
    )
    return account

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: Account = Depends(get_current_active_user)
):
    return current_user

@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_password(
    request: PasswordChangeRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password not set for this account"
        )
    
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/password/reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset. Generates token and stores it (in production, send email)."""
    account = db.query(Account).filter(Account.email == request.email).first()
    
    # Always return success to prevent email enumeration
    if not account:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    account.password_reset_token = reset_token
    account.password_reset_expires = expires_at
    db.commit()
    
    # In production, send email with reset link
    # For now, return token (remove in production!)
    return {
        "message": "Password reset token generated",
        "token": reset_token,  # Remove this in production!
        "expires_at": expires_at.isoformat()
    }

@router.post("/password/reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    account = db.query(Account).filter(
        Account.password_reset_token == request.token
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if not account.password_reset_expires or account.password_reset_expires < datetime.now(timezone.utc):
        account.password_reset_token = None
        account.password_reset_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    account.password_hash = get_password_hash(request.new_password)
    account.password_reset_token = None
    account.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/email/verification/request", status_code=status.HTTP_200_OK)
async def request_email_verification(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Request email verification. Generates token and stores it (in production, send email)."""
    account = db.query(Account).filter(Account.email == request.email).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.email_verified:
        return {"message": "Email is already verified"}
    
    # Generate verification token
    verification_token = generate_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    account.email_verification_token = verification_token
    account.email_verification_expires = expires_at
    db.commit()
    
    # In production, send email with verification link
    # For now, return token (remove in production!)
    return {
        "message": "Verification token generated",
        "token": verification_token,  # Remove this in production!
        "expires_at": expires_at.isoformat()
    }

@router.post("/email/verification/confirm", status_code=status.HTTP_200_OK)
async def confirm_email_verification(
    request: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """Confirm email verification with token."""
    account = db.query(Account).filter(
        Account.email_verification_token == request.token
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    if not account.email_verification_expires or account.email_verification_expires < datetime.now(timezone.utc):
        account.email_verification_token = None
        account.email_verification_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    account.email_verified = True
    account.email_verification_token = None
    account.email_verification_expires = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.put("/profile", response_model=UserOut)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    # Update first name
    if request.firstName is not None:
        current_user.first_name = request.firstName
    
    # Update last name
    if request.lastName is not None:
        current_user.last_name = request.lastName
    
    # Update phone number
    if request.phone is not None:
        current_user.phone_number = request.phone
    
    # Update country
    if request.country is not None:
        current_user.country = request.country
        # If country changes, clear state if it's not valid for new country
        if request.state is None:
            current_user.state = None
    
    # Update state
    if request.state is not None:
        current_user.state = request.state
    
    db.commit()
    db.refresh(current_user)
    return current_user

