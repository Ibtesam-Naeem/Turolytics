# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
import logging

from ..schemas import APIResponse, VehicleMappingRequest, VehicleMappingUpdateRequest
from core.database import get_db
from core.database.models import BouncieVehicleMapping, Account, Vehicle
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .dependencies import _get_vehicle_name, _build_mapping_out, _check_mapping_exists

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ VEHICLE MAPPING ROUTES ------------------------------

@router.get("/mappings", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving vehicle mappings")
async def get_vehicle_mappings(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored vehicle mappings (Turo vehicles linked to Bouncie IMEIs)."""
    query = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).order_by(BouncieVehicleMapping.id.desc())
    
    total = query.count()
    
    mappings = query.offset(offset).limit(limit).all()
    
    vehicle_ids = list({mapping.vehicle_id for mapping in mappings if mapping.vehicle_id})
    vehicle_dict = {}
    if vehicle_ids:
        vehicles = db.query(Vehicle.id, Vehicle.name).filter(
            Vehicle.id.in_(vehicle_ids),
            Vehicle.account_id == current_user.id
        ).all()
        vehicle_dict = {v.id: v.name for v in vehicles}
    
    mappings_data = [
        _build_mapping_out(mapping, vehicle_dict.get(mapping.vehicle_id))
        for mapping in mappings
    ]
    
    return APIResponse(
        success=True,
        data={
            "mappings": mappings_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving mapping detail")
async def get_vehicle_mapping_detail(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific vehicle mapping by ID."""
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    
    return APIResponse(
        success=True,
        data={"mapping": _build_mapping_out(mapping, _get_vehicle_name(db, mapping.vehicle_id, current_user.id))}
    )

@router.post("/mappings", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("creating vehicle mapping", rollback_db=True)
async def create_vehicle_mapping(
    request: VehicleMappingRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new vehicle mapping (link Turo vehicle to Bouncie IMEI)."""
    normalized_imei = (request.imei or "").strip().replace("-", "").replace(" ", "")
    
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == request.vehicle_id,
        Vehicle.account_id == current_user.id
    ).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle {request.vehicle_id} not found for this account"
        )
    
    existing_mapping = _check_mapping_exists(db, current_user.id, vehicle_id=request.vehicle_id)
    if existing_mapping:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping (ID: {existing_mapping.id})"
        )
    
    existing_imei = _check_mapping_exists(db, current_user.id, imei=normalized_imei)
    if existing_imei:
        raise HTTPException(
            status_code=400,
            detail=f"IMEI {normalized_imei} is already mapped to vehicle {existing_imei.vehicle_id}"
        )
    
    mapping = BouncieVehicleMapping(
        account_id=current_user.id,
        vehicle_id=request.vehicle_id,
        imei=normalized_imei,
        bouncie_nickname=request.bouncie_nickname,
        bouncie_vin=request.bouncie_vin
    )
    
    db.add(mapping)
    try:
        db.commit()
        db.refresh(mapping)
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'uq_account_vehicle' in error_str:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping"
            )
        elif 'uq_account_imei' in error_str:
            raise HTTPException(
                status_code=400,
                detail=f"IMEI {normalized_imei} is already mapped to another vehicle"
            )
        raise HTTPException(
            status_code=400,
            detail="Duplicate mapping detected. This vehicle or IMEI is already mapped."
        )
    
    logger.info(f"Created vehicle mapping: vehicle_id={request.vehicle_id}, imei={normalized_imei}")
    
    return APIResponse(
        success=True,
        data={
            "mapping": _build_mapping_out(mapping, vehicle.name),
            "message": "Vehicle mapping created successfully"
        }
    )

@router.put("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("updating vehicle mapping", rollback_db=True)
async def update_vehicle_mapping(
    mapping_id: int = Path(..., description="Mapping ID"),
    request: VehicleMappingUpdateRequest = ...,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing vehicle mapping."""
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    
    if request.vehicle_id is not None and request.vehicle_id != mapping.vehicle_id:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == request.vehicle_id,
            Vehicle.account_id == current_user.id
        ).first()
        
        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle {request.vehicle_id} not found for this account"
            )
        
        existing_mapping = _check_mapping_exists(db, current_user.id, vehicle_id=request.vehicle_id, exclude_id=mapping_id)
        if existing_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping (ID: {existing_mapping.id})"
            )
        
        mapping.vehicle_id = request.vehicle_id
    
    if request.imei is not None and request.imei != mapping.imei:
        normalized_imei = (request.imei or "").strip().replace("-", "").replace(" ", "")
        if normalized_imei != mapping.imei:
            existing_imei = _check_mapping_exists(db, current_user.id, imei=normalized_imei, exclude_id=mapping_id)
            if existing_imei:
                raise HTTPException(
                    status_code=400,
                    detail=f"IMEI {normalized_imei} is already mapped to vehicle {existing_imei.vehicle_id}"
                )
            
            mapping.imei = normalized_imei
    
    if request.bouncie_nickname is not None:
        mapping.bouncie_nickname = request.bouncie_nickname
    
    if request.bouncie_vin is not None:
        mapping.bouncie_vin = request.bouncie_vin
    
    try:
        db.commit()
        db.refresh(mapping)
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'uq_account_vehicle' in error_str:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle {mapping.vehicle_id} already has a Bouncie mapping"
            )
        elif 'uq_account_imei' in error_str:
            raise HTTPException(
                status_code=400,
                detail=f"IMEI {mapping.imei} is already mapped to another vehicle"
            )
        raise HTTPException(
            status_code=400,
            detail="Duplicate mapping detected. This vehicle or IMEI is already mapped."
        )
    
    logger.info(f"Updated vehicle mapping {mapping_id}")
    
    return APIResponse(
        success=True,
        data={
            "mapping": _build_mapping_out(mapping, _get_vehicle_name(db, mapping.vehicle_id, current_user.id)),
            "message": "Vehicle mapping updated successfully"
        }
    )

@router.delete("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("deleting vehicle mapping", rollback_db=True)
async def delete_vehicle_mapping(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a vehicle mapping."""
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    
    vehicle_id = mapping.vehicle_id
    imei = mapping.imei
    
    db.delete(mapping)
    db.commit()
    
    logger.info(f"Deleted vehicle mapping {mapping_id} (vehicle_id={vehicle_id}, imei={imei})")
    
    return APIResponse(
        success=True,
        data={
            "message": f"Vehicle mapping {mapping_id} deleted successfully",
            "deleted_mapping": {
                "id": mapping_id,
                "vehicle_id": vehicle_id,
                "imei": imei
            }
        }
    )

# ------------------------------ END OF FILE ------------------------------