# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional
import logging
from datetime import datetime, timezone

from ..schemas import APIResponse
from core.database import get_db
from core.database.models import BouncieDTCCode, Account, Vehicle, BouncieVehicleMapping
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session
from .dependencies import _get_vehicle_name, _build_dtc_code_out

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ DTC CODE ROUTES ------------------------------

@router.get("/dtc-codes", response_model=APIResponse, tags=["Diagnostics"])
@handle_route_errors("retrieving DTC codes")
async def get_dtc_codes(
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    imei: Optional[str] = Query(None, description="Filter by IMEI"),
    active_only: bool = Query(True, description="Only return active codes"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored DTC codes for authenticated user."""
    query = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == current_user.id
    )
    
    if vehicle_id is not None:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == vehicle_id,
            Vehicle.account_id == current_user.id
        ).first()
        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle {vehicle_id} not found for this account"
            )
        query = query.filter(BouncieDTCCode.vehicle_id == vehicle_id)
    
    if imei:
        normalized_imei = imei.strip().replace("-", "").replace(" ", "")
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == current_user.id,
            BouncieVehicleMapping.imei == normalized_imei
        ).first()
        if not mapping:
            return APIResponse(
                success=True,
                data={
                    "codes": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset
                }
            )
        query = query.filter(BouncieDTCCode.imei == normalized_imei)
    
    if active_only:
        query = query.filter(BouncieDTCCode.is_active.is_(True))
    
    total = query.count()
    
    codes = query.order_by(
        BouncieDTCCode.occurred_at.desc(),
        BouncieDTCCode.id.desc()
    ).offset(offset).limit(limit).all()
    
    vehicle_ids = list({code.vehicle_id for code in codes if code.vehicle_id})
    vehicle_dict = {}
    if vehicle_ids:
        vehicles = db.query(Vehicle.id, Vehicle.name).filter(
            Vehicle.id.in_(vehicle_ids),
            Vehicle.account_id == current_user.id
        ).all()
        vehicle_dict = {v.id: v.name for v in vehicles}
    
    codes_data = [
        _build_dtc_code_out(code, vehicle_dict.get(code.vehicle_id))
        for code in codes
    ]
    
    return APIResponse(
        success=True,
        data={
            "codes": codes_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.post("/dtc-codes/{code_id}/clear", response_model=APIResponse, tags=["Diagnostics"])
@handle_route_errors("clearing DTC code", rollback_db=True)
async def clear_dtc_code(
    code_id: int = Path(..., description="DTC code ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a DTC code as cleared."""
    code = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.id == code_id,
        BouncieDTCCode.account_id == current_user.id
    ).first()
    
    if not code:
        raise HTTPException(status_code=404, detail=f"DTC code {code_id} not found")
    
    vehicle_name = _get_vehicle_name(db, code.vehicle_id, current_user.id)
    
    if not code.is_active:
        return APIResponse(
            success=True,
            data={"message": "Code already cleared", "code": _build_dtc_code_out(code, vehicle_name)}
        )
    
    code.is_active = False
    code.cleared_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(code)
    
    logger.info(f"Cleared DTC code {code.code} for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "message": "DTC code cleared successfully",
            "code": _build_dtc_code_out(code, vehicle_name)
        }
    )

# ------------------------------ END OF FILE ------------------------------