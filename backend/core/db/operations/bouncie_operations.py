# ------------------------------ IMPORTS ------------------------------
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, List

from sqlalchemy.orm import Session

from core.db.base import Account, BouncieDevice, BouncieEvent, BouncieTrip
from core.db.database import get_db_session

# ------------------------------ ACCOUNT HELPERS ------------------------------

def get_or_create_account(email: str) -> Optional[int]:
    """Get or create an account by email (reuse Turo accounts table)."""
    with get_db_session() as db:
        acct = db.query(Account).filter(Account.turo_email == email).first()
        if acct:
            return acct.id
        new_acct = Account(turo_email=email, is_active=True)
        db.add(new_acct)
        db.commit()
        db.refresh(new_acct)
        return new_acct.id

# ------------------------------ DEVICE UPSERT ------------------------------

def _upsert_device(db: Session, account_id: int, vehicle: dict[str, Any]) -> str:
    """Upsert a BouncieDevice row from a single vehicle dict."""
    imei = vehicle.get("imei")
    if not imei:
        return "skipped"

    existing: Optional[BouncieDevice] = (
        db.query(BouncieDevice)
        .filter(BouncieDevice.account_id == account_id, BouncieDevice.imei == imei)
        .first()
    )

    model = vehicle.get("model", {})
    stats = vehicle.get("stats", {})
    location = stats.get("location") or {}
    mil = stats.get("mil") or {}
    battery = stats.get("battery") or {}

    last_updated = stats.get("lastUpdated")
    try:
        last_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00")) if last_updated else None
    except Exception:
        last_dt = None

    common_fields = dict(
        vin=vehicle.get("vin"),
        nickname=vehicle.get("nickName"),
        make=model.get("make"),
        model=model.get("name"),
        year=model.get("year"),
        last_updated=last_dt,
        odometer=stats.get("odometer"),
        location_lat=location.get("lat"),
        location_lon=location.get("lon"),
        heading=location.get("heading"),
        fuel_level=stats.get("fuelLevel"),
        is_running=stats.get("isRunning"),
        speed=stats.get("speed"),
        battery_status=battery.get("status"),
        mil_on=mil.get("milOn"),
        stats=stats,
        raw=vehicle,
    )

    if existing:
        for k, v in common_fields.items():
            setattr(existing, k, v)
        return "updated"
    else:
        row = BouncieDevice(account_id=account_id, imei=imei, **common_fields)
        db.add(row)
        return "created"

def save_bouncie_snapshot(account_email: str, vehicles_payload: dict[str, Any]) -> dict[str, int]:
    """Persist current Bouncie vehicles snapshot for an account.

    vehicles_payload is expected to be the `vehicles` array like the API returns.
    """
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {"devices_processed": 0, "created": 0, "updated": 0}

    with get_db_session() as db:
        created = updated = processed = 0
        vehicles = vehicles_payload if isinstance(vehicles_payload, list) else vehicles_payload.get("vehicles") or []
        for v in vehicles:
            result = _upsert_device(db, account_id, v)
            if result in ("created", "updated"):
                processed += 1
                if result == "created":
                    created += 1
                else:
                    updated += 1
        db.commit()
        return {"devices_processed": processed, "created": created, "updated": updated}

# ------------------------------ WEBHOOK EVENT STORAGE ------------------------------

def store_bouncie_event(account_email: Optional[str], event_type: str, payload: dict[str, Any], signature: Optional[str]) -> int:
    """Store a webhook event for audit and optional replay."""
    account_id = get_or_create_account(account_email) if account_email else None
    event_time = payload.get("timestamp")
    try:
        event_dt = datetime.fromisoformat(event_time.replace("Z", "+00:00")) if event_time else None
    except Exception:
        event_dt = None

    device_imei = None
    data = payload.get("data") or {}
    if isinstance(data, dict):
        device_imei = data.get("imei") or data.get("device", {}).get("imei")

    with get_db_session() as db:
        evt = BouncieEvent(
            account_id=account_id,
            event_type=event_type,
            event_timestamp=event_dt,
            device_imei=device_imei,
            data=data,
            signature=signature,
            raw_payload=payload,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)
        return evt.id

# ------------------------------ TRIP OPERATIONS ------------------------------

def _upsert_trip(db: Session, account_id: int, trip_data: dict[str, Any]) -> str:
    """Upsert a BouncieTrip row from a single trip dict."""
    transaction_id = trip_data.get("transactionId")
    imei = trip_data.get("imei")
    
    if not transaction_id or not imei:
        return "skipped"
    
    existing: Optional[BouncieTrip] = (
        db.query(BouncieTrip)
        .filter(BouncieTrip.account_id == account_id, BouncieTrip.transaction_id == transaction_id)
        .first()
    )
    
    start_time = trip_data.get("startTime")
    end_time = trip_data.get("endTime")
    
    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")) if start_time else None
    except Exception:
        start_dt = None
    
    try:
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None
    except Exception:
        end_dt = None
    
    common_fields = dict(
        imei=imei,
        transaction_id=transaction_id,
        start_time=start_dt,
        end_time=end_dt,
        timezone=trip_data.get("timeZone"),
        distance=trip_data.get("distance"),
        average_speed=trip_data.get("averageSpeed"),
        max_speed=trip_data.get("maxSpeed"),
        fuel_consumed=trip_data.get("fuelConsumed"),
        start_odometer=trip_data.get("startOdometer"),
        end_odometer=trip_data.get("endOdometer"),
        total_idle_duration=trip_data.get("totalIdleDuration"),
        hard_braking_count=trip_data.get("hardBrakingCount"),
        hard_acceleration_count=trip_data.get("hardAccelerationCount"),
        gps_format=trip_data.get("gpsFormat"),
        gps_data=trip_data.get("gpsData"),
        raw_data=trip_data,
    )
    
    if existing:
        for k, v in common_fields.items():
            setattr(existing, k, v)
        return "updated"
    else:
        row = BouncieTrip(account_id=account_id, **common_fields)
        db.add(row)
        return "created"

def save_bouncie_trips(account_email: str, trips_data: List[dict[str, Any]]) -> dict[str, int]:
    """Save Bouncie trips data to the database.
    
    Args:
        account_email: Account email to associate trips with
        trips_data: List of trip dictionaries from Bouncie API
        
    Returns:
        Dictionary with counts of processed, created, and updated trips
    """
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {"trips_processed": 0, "created": 0, "updated": 0}
    
    with get_db_session() as db:
        created = updated = processed = 0
        
        for trip in trips_data:
            result = _upsert_trip(db, account_id, trip)
            if result in ("created", "updated"):
                processed += 1
                if result == "created":
                    created += 1
                else:
                    updated += 1
        
        db.commit()
        return {"trips_processed": processed, "created": created, "updated": updated}

def get_bouncie_trips(account_email: str, imei: Optional[str] = None, limit: int = 100) -> List[dict[str, Any]]:
    """Get Bouncie trips for an account.
    
    Args:
        account_email: Account email
        imei: Optional IMEI filter
        limit: Maximum number of trips to return
        
    Returns:
        List of trip dictionaries
    """
    account_id = get_or_create_account(account_email)
    if not account_id:
        return []
    
    with get_db_session() as db:
        query = db.query(BouncieTrip).filter(BouncieTrip.account_id == account_id)
        
        if imei:
            query = query.filter(BouncieTrip.imei == imei)
        
        trips = query.order_by(BouncieTrip.start_time.desc()).limit(limit).all()
        
        return [trip.to_dict() for trip in trips]

def get_bouncie_trip_stats(account_email: str, imei: Optional[str] = None, days: int = 30) -> dict[str, Any]:
    """Get trip statistics for an account.
    
    Args:
        account_email: Account email
        imei: Optional IMEI filter
        days: Number of days to look back
        
    Returns:
        Dictionary with trip statistics
    """
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {}
    
    with get_db_session() as db:
        from datetime import datetime, timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        query = db.query(BouncieTrip).filter(
            BouncieTrip.account_id == account_id,
            BouncieTrip.start_time >= start_date
        )
        
        if imei:
            query = query.filter(BouncieTrip.imei == imei)
        
        trips = query.all()
        
        if not trips:
            return {"total_trips": 0, "total_distance": 0, "total_fuel": 0, "avg_speed": 0, "max_speed": 0}
        
        total_distance = sum(trip.distance or 0 for trip in trips)
        total_fuel = sum(trip.fuel_consumed or 0 for trip in trips)
        avg_speed = sum(trip.average_speed or 0 for trip in trips) / len(trips)
        max_speed = max(trip.max_speed or 0 for trip in trips)
        
        return {
            "total_trips": len(trips),
            "total_distance": total_distance,
            "total_fuel": total_fuel,
            "avg_speed": avg_speed,
            "max_speed": max_speed,
            "days_analyzed": days
        }

# ------------------------------ END OF FILE ------------------------------