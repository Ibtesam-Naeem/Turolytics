# ------------------------------ IMPORTS ------------------------------
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.db.base import Account, BouncieDevice, BouncieEvent
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

# ------------------------------ END OF FILE ------------------------------