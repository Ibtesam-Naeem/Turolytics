# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List
import logging
from sqlalchemy.orm import Session

from core.database import get_db
from core.database.models.account import Account
from core.database.models.roi_calculation import ROICalculation
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from .schemas import (
    ROICalculationCreate,
    ROICalculationUpdate,
    ROICalculationOut,
    APIResponse,
)

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ ROI CALCULATION ROUTES ------------------------------

@router.get("/calculations", response_model=APIResponse, tags=["ROI Calculator"])
@handle_route_errors("getting ROI calculations")
async def get_roi_calculations(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Get all ROI calculations for the authenticated user."""
    calculations = db.query(ROICalculation).filter(
        ROICalculation.account_id == current_user.id
    ).order_by(ROICalculation.created_at.desc()).all()
    
    return APIResponse(
        success=True,
        data={
            "calculations": [ROICalculationOut.model_validate(calc, from_attributes=True).model_dump() for calc in calculations],
            "total": len(calculations)
        }
    )

@router.post("/calculations", response_model=APIResponse, tags=["ROI Calculator"])
@handle_route_errors("creating ROI calculation")
async def create_roi_calculation(
    calculation: ROICalculationCreate,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Create a new ROI calculation."""
    new_calculation = ROICalculation(
        account_id=current_user.id,
        vehicle_name=calculation.vehicle_name,
        vehicle_price=calculation.vehicle_price,
        daily_rate=calculation.daily_rate,
        booking_days=calculation.booking_days,
        monthly_expenses=calculation.monthly_expenses,
        insurance_monthly=calculation.insurance_monthly,
        annual_depreciation=calculation.annual_depreciation,
        roi=calculation.roi,
        annual_profit=calculation.annual_profit,
    )
    
    db.add(new_calculation)
    db.commit()
    db.refresh(new_calculation)
    
    logger.info(f"Created ROI calculation {new_calculation.id} for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "calculation": ROICalculationOut.model_validate(new_calculation, from_attributes=True).model_dump()
        }
    )

@router.patch("/calculations/{calculation_id}", response_model=APIResponse, tags=["ROI Calculator"])
@handle_route_errors("updating ROI calculation")
async def update_roi_calculation(
    calculation_id: int = Path(..., description="ROI calculation ID"),
    calculation_update: ROICalculationUpdate = ...,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update an existing ROI calculation."""
    calculation = db.query(ROICalculation).filter(
        ROICalculation.id == calculation_id,
        ROICalculation.account_id == current_user.id
    ).first()
    
    if not calculation:
        raise HTTPException(status_code=404, detail=f"ROI calculation {calculation_id} not found")
    
    # Update only provided fields
    update_data = calculation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(calculation, field, value)
    
    db.commit()
    db.refresh(calculation)
    
    logger.info(f"Updated ROI calculation {calculation_id} for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "calculation": ROICalculationOut.model_validate(calculation, from_attributes=True).model_dump()
        }
    )

@router.delete("/calculations/{calculation_id}", response_model=APIResponse, tags=["ROI Calculator"])
@handle_route_errors("deleting ROI calculation")
async def delete_roi_calculation(
    calculation_id: int = Path(..., description="ROI calculation ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """Delete an ROI calculation."""
    calculation = db.query(ROICalculation).filter(
        ROICalculation.id == calculation_id,
        ROICalculation.account_id == current_user.id
    ).first()
    
    if not calculation:
        raise HTTPException(status_code=404, detail=f"ROI calculation {calculation_id} not found")
    
    db.delete(calculation)
    db.commit()
    
    logger.info(f"Deleted ROI calculation {calculation_id} for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={"message": f"ROI calculation {calculation_id} deleted successfully"}
    )
