#!/usr/bin/env python3
"""
Fix Bouncie vehicle mapping - move mapping from vehicle 1 (Genesis) to vehicle 2 (Elantra).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import SessionLocal
from core.database.models import Vehicle, BouncieVehicleMapping, Account

def fix_mapping():
    db = SessionLocal()
    
    try:
        # Get first account
        account = db.query(Account).first()
        if not account:
            print("❌ No accounts found")
            return
        
        print(f"✓ Using account: {account.email} (ID: {account.id})")
        
        # Get all vehicles
        vehicles = db.query(Vehicle).filter(Vehicle.account_id == account.id).order_by(Vehicle.id).all()
        print(f"\n✓ Found {len(vehicles)} vehicle(s):")
        for v in vehicles:
            print(f"  - Vehicle ID {v.id}: {v.name}")
        
        # Get current mapping
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if not mapping:
            print("\n❌ No Bouncie mapping found")
            return
        
        print(f"\n✓ Current mapping:")
        print(f"  - Mapping ID: {mapping.id}")
        print(f"  - IMEI: {mapping.imei}")
        print(f"  - Current vehicle_id: {mapping.vehicle_id}")
        
        current_vehicle = db.query(Vehicle).filter(Vehicle.id == mapping.vehicle_id).first()
        print(f"  - Current vehicle: {current_vehicle.name if current_vehicle else 'Unknown'}")
        
        # Find Elantra (vehicle_id=2)
        elantra = db.query(Vehicle).filter(
            Vehicle.id == 2,
            Vehicle.account_id == account.id
        ).first()
        
        if not elantra:
            print("\n❌ Elantra (vehicle_id=2) not found")
            return
        
        print(f"\n✓ Target vehicle:")
        print(f"  - Vehicle ID: {elantra.id}")
        print(f"  - Name: {elantra.name}")
        
        # Check if Elantra already has a mapping
        existing_elantra_mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.vehicle_id == elantra.id,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if existing_elantra_mapping:
            print(f"\n⚠ Elantra already has a mapping (ID: {existing_elantra_mapping.id})")
            print("   Deleting old mapping...")
            db.delete(existing_elantra_mapping)
        
        # Update mapping to point to Elantra
        print(f"\n✓ Updating mapping to point to Elantra (vehicle_id={elantra.id})...")
        mapping.vehicle_id = elantra.id
        db.commit()
        db.refresh(mapping)
        
        print(f"\n✅ Mapping updated successfully!")
        print(f"  - Mapping ID: {mapping.id}")
        print(f"  - IMEI: {mapping.imei}")
        print(f"  - Vehicle ID: {mapping.vehicle_id}")
        print(f"  - Vehicle: {elantra.name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  Fix Bouncie Vehicle Mapping")
    print("=" * 80)
    fix_mapping()
    print("\n" + "=" * 80)
    print("  Complete")
    print("=" * 80 + "\n")

