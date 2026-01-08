#!/usr/bin/env python3
"""
Database Dump Script
Dumps all database contents to a text file.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import inspect
from sqlalchemy.orm import Session


# Ensure `backend/` is on sys.path so `import core...` works from any CWD.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from core.database.connection import SessionLocal, engine  # noqa: E402
from core.database.models import (  # noqa: E402
    Account,
    AccountDeletionLog,
    BouncieIntegration,
    BouncieVehicleMapping,
    BouncieTripMatch,
    BouncieDTCCode,
    BouncieWebhookLog,
    TuroIntegration,
    Vehicle,
    VehicleUtilizationHistory,
    Trip,
    Review,
    EarningsBreakdown,
    VehicleEarnings,
    SessionStorage,
    Document,
)


def serialize_value(value: Any) -> str:
    """Convert a value to a string representation."""
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    if isinstance(value, bytes):
        return f"<binary data: {len(value)} bytes>"
    return str(value)


def get_table_data(db: Session, model_class: type) -> List[Dict[str, Any]]:
    """Get all records from a table."""
    try:
        records = db.query(model_class).all()
        data = []
        for record in records:
            inspector = inspect(model_class)
            row_dict: Dict[str, Any] = {}
            for column in inspector.columns:
                row_dict[column.name] = getattr(record, column.name, None)
            data.append(row_dict)
        return data
    except Exception as e:
        return [{"error": f"Failed to query table: {str(e)}"}]


def get_table_name(model_class: type) -> str:
    """Get the table name from a model class."""
    return model_class.__tablename__ if hasattr(model_class, "__tablename__") else model_class.__name__


def format_table_dump(table_name: str, data: List[Dict[str, Any]], output_lines: List[str]) -> None:
    """Format and add table data to output lines."""
    output_lines.append("=" * 80)
    output_lines.append(f"TABLE: {table_name.upper()}")
    output_lines.append("=" * 80)
    output_lines.append(f"Total Records: {len(data)}")
    output_lines.append("")

    if not data:
        output_lines.append("(No records found)")
        output_lines.append("")
        return

    if "error" in data[0]:
        output_lines.append(f"ERROR: {data[0]['error']}")
        output_lines.append("")
        return

    # Get all column names
    all_columns = set()
    for row in data:
        all_columns.update(row.keys())
    columns = sorted(all_columns)

    # Print header
    header = " | ".join([col.ljust(20) for col in columns])
    output_lines.append(header)
    output_lines.append("-" * len(header))

    for idx, row in enumerate(data, 1):
        row_values = []
        for col in columns:
            value = serialize_value(row.get(col))
            if len(value) > 50:
                value = value[:47] + "..."
            row_values.append(value.ljust(20))
        output_lines.append(" | ".join(row_values))

        # Detailed view for each record
        output_lines.append("")
        output_lines.append(f"  Record #{idx} Details:")
        for col in columns:
            value = row.get(col)
            formatted_value = serialize_value(value)
            if isinstance(value, (dict, list)) or (isinstance(value, str) and len(value) > 100):
                output_lines.append(f"    {col}:")
                for line in formatted_value.split("\n"):
                    output_lines.append(f"      {line}")
            else:
                output_lines.append(f"    {col}: {formatted_value}")
        output_lines.append("")

    output_lines.append("")


def dump_database(output_file: str = "database_dump.txt") -> None:
    """Dump all database contents to a text file."""
    db: Session = SessionLocal()
    try:
        output_lines: List[str] = []
        output_lines.append("=" * 80)
        output_lines.append("DATABASE DUMP")
        output_lines.append("=" * 80)
        output_lines.append(f"Generated: {datetime.now().isoformat()}")
        output_lines.append(f"Database URL: {engine.url}")
        output_lines.append("")
        output_lines.append("")

        models = [
            Account,
            AccountDeletionLog,
            TuroIntegration,
            BouncieIntegration,
            BouncieVehicleMapping,
            BouncieTripMatch,
            BouncieDTCCode,
            BouncieWebhookLog,
            Vehicle,
            VehicleUtilizationHistory,
            Trip,
            Review,
            EarningsBreakdown,
            VehicleEarnings,
            SessionStorage,
            Document,
        ]

        for model in models:
            table_name = get_table_name(model)
            print(f"Dumping table: {table_name}...")
            data = get_table_data(db, model)
            format_table_dump(table_name, data, output_lines)

        output_content = "\n".join(output_lines)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_content)

        print("\nDatabase dump completed successfully!")
        print(f"Output file: {output_file}")
        print(f"Total size: {len(output_content)} bytes")
    except Exception as e:
        print(f"Error during database dump: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "database_dump.txt"
    print("Starting database dump...")
    dump_database(output_file)
    print("Done!")



