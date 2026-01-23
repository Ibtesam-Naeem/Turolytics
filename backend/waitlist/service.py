# ------------------------------ IMPORTS ------------------------------
from dataclasses import dataclass
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from core.database.models.waitlist import Waitlist
from core.services.email_service import EmailService
from core.utils.route_helpers import update_resource_fields
from .schemas import WaitlistRequest

logger = logging.getLogger(__name__)

# ------------------------------ CONSTANTS ------------------------------

FIELD_MAPPING = {
    "vehicleCount": "vehicle_count",
    "trackingProduct": "tracking_product",
    "trackingProductOther": "tracking_product_other",
    "wouldUse": "would_use",
    "priceWilling": "price_willing",
    "feedback": "feedback"
}

# ------------------------------ RESPONSE MODELS ------------------------------

@dataclass
class JoinWaitlistResult:
    """Result of joining the waitlist."""
    message: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API response."""
        return {
            "message": self.message
        }

# ------------------------------ SERVICE ------------------------------

class WaitlistService:
    """Service for managing waitlist operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_request_data(self, request_dict: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """Extract field data from request dict as snake_case dict."""
        return {
            db_field: request_dict.get(req_field)
            for req_field, db_field in FIELD_MAPPING.items()
            if request_dict.get(req_field) is not None
        }
    
    def _get_update_data(self, request_dict: Dict[str, Optional[str]], existing: Waitlist) -> Dict[str, Optional[str]]:
        """Get update data (only changed fields) from request dict."""
        return {
            db_field: request_dict.get(req_field)
            for req_field, db_field in FIELD_MAPPING.items()
            if request_dict.get(req_field) is not None
            and request_dict.get(req_field) != getattr(existing, db_field)
        }
    
    def _already_exists(self, existing: Waitlist) -> JoinWaitlistResult:
        """Handle case where entry already exists (same info)."""
        logger.info(f"Waitlist: Email {existing.email} already exists with same info")
        return JoinWaitlistResult(
            message="You're already on the waitlist!"
        )
    
    def _send_confirmation_email(self, email: str, request_dict: Dict[str, Optional[str]]) -> None:
        """Send confirmation email (best-effort, errors are logged but don't fail the request)."""
        try:
            context = self._get_request_data(request_dict)
            result = EmailService.send_waitlist_confirmation(email, context)
            if result.get("success"):
                logger.info(f"Waitlist: Confirmation email sent to {email}")
            else:
                logger.warning(f"Waitlist: Failed to send confirmation email to {email}: {result.get('message')}")
        except Exception as e:
            logger.error(f"Waitlist: Error sending confirmation email to {email}: {e}", exc_info=True)
    
    def join_waitlist(self, request: WaitlistRequest) -> JoinWaitlistResult:
        """Add or update an email in the waitlist."""
        request_dict = request.model_dump(exclude={"email"})
        email = request.email
        
        try:
            existing = self.db.query(Waitlist).filter(Waitlist.email == email).first()
            
            if existing:
                update_data = self._get_update_data(request_dict, existing)
                
                if update_data:
                    update_resource_fields(self.db, existing, update_data, commit=False)
                    self.db.commit()
                    self.db.refresh(existing)
                    logger.info(f"Waitlist: Updated existing entry for {email}")
                    return JoinWaitlistResult(
                        message="Your waitlist information has been updated!"
                    )
                
                return self._already_exists(existing)
            
            entry_data = self._get_request_data(request_dict)
            waitlist_entry = Waitlist(email=email, **entry_data)
            self.db.add(waitlist_entry)
            self.db.commit()
            self.db.refresh(waitlist_entry)
            
            logger.info(f"Waitlist: Added email {email}")
            
            self._send_confirmation_email(email, request_dict)
            
            return JoinWaitlistResult(
                message="Successfully joined the waitlist!"
            )
        except IntegrityError as e:
            self.db.rollback()
            existing = self.db.query(Waitlist).filter(Waitlist.email == email).first()
            if existing:
                logger.info(f"Waitlist: Race condition - email {email} was created by another request")
                return self._already_exists(existing)
            logger.error(f"Waitlist: IntegrityError but couldn't find entry for {email}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error joining waitlist: {e}", exc_info=True)
            raise
    
    def get_all_entries(self) -> List[Dict[str, Optional[str]]]:
        """Get all waitlist entries."""
        try:
            entries = self.db.query(Waitlist).order_by(Waitlist.created_at.desc()).all()
            return [
                {
                    "id": entry.id,
                    "email": entry.email,
                    "vehicle_count": entry.vehicle_count,
                    "tracking_product": entry.tracking_product,
                    "tracking_product_other": entry.tracking_product_other,
                    "would_use": entry.would_use,
                    "price_willing": entry.price_willing,
                    "feedback": entry.feedback,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "notified_at": entry.notified_at.isoformat() if entry.notified_at else None,
                }
                for entry in entries
            ]
        except Exception as e:
            logger.error(f"Error fetching waitlist entries: {e}", exc_info=True)
            raise