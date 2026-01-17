# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import logging

from core.database import get_db
from core.database.models.waitlist import Waitlist
from core.database.models import Account
from core.services.email_service import EmailService
from core.security.auth import get_current_active_user

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ SCHEMAS ------------------------------

class WaitlistRequest(BaseModel):
    email: EmailStr
    vehicleCount: Optional[str] = None
    trackingProduct: Optional[str] = None
    trackingProductOther: Optional[str] = None
    wouldUse: Optional[str] = None
    priceWilling: Optional[str] = None
    feedback: Optional[str] = None

class WaitlistResponse(BaseModel):
    success: bool
    message: str
    position: Optional[int] = None  # User's position in the waitlist
    total: Optional[int] = None  # Total number of people on waitlist

class WaitlistEntryOut(BaseModel):
    id: int
    email: str
    vehicle_count: Optional[str] = None
    tracking_product: Optional[str] = None
    tracking_product_other: Optional[str] = None
    would_use: Optional[str] = None
    price_willing: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime
    notified_at: Optional[datetime] = None

class WaitlistListResponse(BaseModel):
    success: bool
    entries: List[WaitlistEntryOut]
    total: int
    page: int
    page_size: int

class BulkEmailResponse(BaseModel):
    success: bool
    message: str
    total_recipients: int
    sent_count: int
    failed_count: int
    failed_emails: List[str] = []

# ------------------------------ ROUTES ------------------------------

@router.post("/waitlist", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    request: WaitlistRequest,
    db: Session = Depends(get_db)
):
    """
    Add an email to the waitlist.
    Returns success if email is added, or if email already exists.
    """
    try:
        # Check if email already exists
        existing = db.query(Waitlist).filter(Waitlist.email == request.email).first()
        
        if existing:
            # Update existing entry with new optional info (if provided)
            updated = False
            if request.vehicleCount and request.vehicleCount != existing.vehicle_count:
                existing.vehicle_count = request.vehicleCount
                updated = True
            if request.trackingProduct and request.trackingProduct != existing.tracking_product:
                existing.tracking_product = request.trackingProduct
                updated = True
            if request.trackingProductOther and request.trackingProductOther != existing.tracking_product_other:
                existing.tracking_product_other = request.trackingProductOther
                updated = True
            if request.wouldUse and request.wouldUse != existing.would_use:
                existing.would_use = request.wouldUse
                updated = True
            if request.priceWilling and request.priceWilling != existing.price_willing:
                existing.price_willing = request.priceWilling
                updated = True
            if request.feedback and request.feedback != existing.feedback:
                existing.feedback = request.feedback
                updated = True
            
            if updated:
                db.commit()
                db.refresh(existing)
                # Calculate position for existing entry
                position = db.query(Waitlist).filter(Waitlist.created_at <= existing.created_at).count()
                total = db.query(Waitlist).count()
                logger.info(f"Waitlist: Updated existing entry for {request.email} (position {position} of {total})")
                return WaitlistResponse(
                    success=True,
                    message="Your waitlist information has been updated!",
                    position=position,
                    total=total
                )
            else:
                # Calculate position for existing entry
                position = db.query(Waitlist).filter(Waitlist.created_at <= existing.created_at).count()
                total = db.query(Waitlist).count()
                logger.info(f"Waitlist: Email {request.email} already exists with same info (position {position} of {total})")
                return WaitlistResponse(
                    success=True,
                    message="You're already on the waitlist!",
                    position=position,
                    total=total
                )
        
        # Create new waitlist entry
        waitlist_entry = Waitlist(
            email=request.email,
            vehicle_count=request.vehicleCount,
            tracking_product=request.trackingProduct,
            tracking_product_other=request.trackingProductOther,
            would_use=request.wouldUse,
            price_willing=request.priceWilling,
            feedback=request.feedback
        )
        db.add(waitlist_entry)
        db.commit()
        db.refresh(waitlist_entry)
        
        # Calculate position: count how many entries were created before or at the same time
        position = db.query(Waitlist).filter(Waitlist.created_at <= waitlist_entry.created_at).count()
        total = db.query(Waitlist).count()
        
        logger.info(f"Waitlist: Added email {request.email} (position {position} of {total})")
        
        # Send confirmation email (non-blocking - don't fail signup if email fails)
        # Only send email for NEW signups, not updates
        try:
            # Pass context with user's form data and position for personalization
            context = {
                "vehicle_count": request.vehicleCount,
                "tracking_product": request.trackingProduct,
                "tracking_product_other": request.trackingProductOther,
                "would_use": request.wouldUse,
                "price_willing": request.priceWilling,
                "feedback": request.feedback,
                "position": position,
                "total": total
            }
            email_result = EmailService.send_waitlist_confirmation(request.email, context)
            if email_result.get("success"):
                logger.info(f"Waitlist: Confirmation email sent to {request.email}")
            else:
                logger.warning(f"Waitlist: Failed to send confirmation email to {request.email}: {email_result.get('message')}")
        except Exception as e:
            # Log error but don't fail the signup
            logger.error(f"Waitlist: Error sending confirmation email to {request.email}: {e}", exc_info=True)
        
        return WaitlistResponse(
            success=True,
            message="Successfully joined the waitlist!",
            position=position,
            total=total
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding to waitlist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join waitlist. Please try again later."
        )

# ------------------------------ ADMIN ROUTES ------------------------------

@router.get("/waitlist/admin", response_model=WaitlistListResponse, tags=["Waitlist Admin"])
async def get_waitlist_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all waitlist entries (admin only)."""
    try:
        query = db.query(Waitlist)
        
        # Search filter
        if search:
            query = query.filter(Waitlist.email.ilike(f"%{search}%"))
        
        # Get total count
        total = query.count()
        
        # Pagination
        offset = (page - 1) * page_size
        entries = query.order_by(desc(Waitlist.created_at)).offset(offset).limit(page_size).all()
        
        return WaitlistListResponse(
            success=True,
            entries=[WaitlistEntryOut.model_validate(e, from_attributes=True) for e in entries],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error fetching waitlist entries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch waitlist entries"
        )

@router.post("/waitlist/admin/send-bulk", response_model=BulkEmailResponse, tags=["Waitlist Admin"])
async def send_bulk_email(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send launch email to all waitlist entries that haven't been notified yet."""
    try:
        from core.services.email_templates import get_launch_email_template
        
        # Get all entries that haven't been notified
        entries = db.query(Waitlist).filter(Waitlist.notified_at.is_(None)).all()
        
        if not entries:
            return BulkEmailResponse(
                success=True,
                message="No pending entries to notify",
                total_recipients=0,
                sent_count=0,
                failed_count=0
            )
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        service = EmailService.get_instance()
        
        for entry in entries:
            try:
                template = get_launch_email_template(entry.email)
                
                result = service.send_email(
                    to_email=entry.email,
                    subject=template["subject"],
                    html_content=template["html_content"],
                    text_content=template["text_content"]
                )
                
                if result.get("success"):
                    entry.notified_at = datetime.now(timezone.utc)
                    sent_count += 1
                    logger.info(f"Bulk email sent to {entry.email}")
                else:
                    failed_count += 1
                    failed_emails.append(entry.email)
                    logger.warning(f"Failed to send bulk email to {entry.email}: {result.get('message')}")
            
            except Exception as e:
                failed_count += 1
                failed_emails.append(entry.email)
                logger.error(f"Error sending bulk email to {entry.email}: {e}", exc_info=True)
        
        db.commit()
        
        return BulkEmailResponse(
            success=True,
            message=f"Bulk email sent to {sent_count} recipients",
            total_recipients=len(entries),
            sent_count=sent_count,
            failed_count=failed_count,
            failed_emails=failed_emails
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending bulk emails: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send bulk emails"
        )
