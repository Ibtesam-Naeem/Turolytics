#!/usr/bin/env python3
"""
Seed database from `backend/database_dump.txt`.

Important constraints (per request):
- Single file seeder (no extra fixtures/migrations created here)
- Uses ONLY existing SQLAlchemy models/tables (no fake tables/rows)
- Uses `database_dump.txt` as the source of truth for rows/values

How it works:
- Parses the "Record #N Details" blocks from `database_dump.txt`
- Converts values to model column types (bool/int/float/datetime/json/array/enum)
- Upserts by primary key (updates existing rows; inserts missing rows)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


# Ensure `backend/` is on sys.path so `import core...` works from any CWD.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from core.database.connection import Base, SessionLocal, engine  # noqa: E402
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
from core.database.models.s3.document import DocumentCategory  # noqa: E402


MODEL_BY_DUMP_TABLE: Dict[str, Type[Any]] = {
    "ACCOUNTS": Account,
    "ACCOUNT_DELETION_LOGS": AccountDeletionLog,
    "TURO_INTEGRATION": TuroIntegration,
    "BOUNCIE_TOKEN": BouncieIntegration,
    "BOUNCIE_VEHICLE_MAPPING": BouncieVehicleMapping,
    "BOUNCIE_TRIP": BouncieTripMatch,
    "BOUNCIE_DTC_CODES": BouncieDTCCode,
    "BOUNCIE_WEBHOOK_LOGS": BouncieWebhookLog,
    "TURO_VEHICLES": Vehicle,
    "TURO_VEHICLE_UTILIZATION_HISTORY": VehicleUtilizationHistory,
    "TURO_TRIPS": Trip,
    "TURO_REVIEWS": Review,
    "EARNINGS_BREAKDOWN": EarningsBreakdown,
    "TURO_VEHICLE_EARNINGS": VehicleEarnings,
    "SESSION_STORAGE": SessionStorage,
    "DOCUMENTS": Document,
}


@dataclass
class ParsedDump:
    # dump-table-name (as shown in file) -> list of record dicts
    tables: Dict[str, List[Dict[str, Any]]]


def _parse_iso_datetime(value: str) -> datetime:
    # dump format is `datetime.isoformat()` so `fromisoformat` works; also support trailing Z
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_scalar(value: str) -> Any:
    """Parse common scalar encodings used by the dump."""
    v = value.strip()
    if v == "NULL":
        return None
    if v == "True":
        return True
    if v == "False":
        return False
    return v


def _parse_record_details(lines: List[str], start_idx: int) -> Tuple[Dict[str, Any], int]:
    """
    Parse a block that starts AFTER the "  Record #N Details:" line.
    Returns (record_dict, next_idx).
    """
    record: Dict[str, Any] = {}
    i = start_idx

    def is_field_line(s: str) -> bool:
        return s.startswith("    ") and ":" in s

    while i < len(lines):
        line = lines[i]
        # End of record details block
        if not line.startswith("    "):
            break

        # Expect: "    key: value" OR "    key:" (block value follows)
        if not is_field_line(line):
            i += 1
            continue

        key_part, rest = line[4:].split(":", 1)
        key = key_part.strip()
        rest_stripped = rest.strip()

        if rest_stripped != "":
            record[key] = _parse_scalar(rest_stripped)
            i += 1
            continue

        # Block value: subsequent lines start with 6 spaces "      "
        i += 1
        block_lines: List[str] = []
        while i < len(lines) and lines[i].startswith("      "):
            block_lines.append(lines[i][6:])
            i += 1

        block_text = "\n".join(block_lines).strip("\n")
        if block_text == "":
            record[key] = None
            continue

        # Try JSON first (dict/list), otherwise treat as plain string.
        try:
            record[key] = json.loads(block_text)
        except Exception:
            record[key] = _parse_scalar(block_text)

    return record, i


def parse_database_dump(dump_path: Path) -> ParsedDump:
    text_content = dump_path.read_text(encoding="utf-8")
    lines = text_content.splitlines()

    tables: Dict[str, List[Dict[str, Any]]] = {}
    current_table: Optional[str] = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("TABLE:"):
            current_table = line.replace("TABLE:", "", 1).strip().upper()
            tables.setdefault(current_table, [])
            i += 1
            continue

        if line.startswith("Record #") or line.startswith("Record #".upper()):
            # (defensive) dump uses "  Record #N Details:" with 2 spaces, but handle variants
            if current_table:
                record, next_i = _parse_record_details(lines, i + 1)
                if record:
                    tables[current_table].append(record)
                i = next_i
                continue

        if lines[i].startswith("  Record #") and "Details:" in lines[i]:
            if current_table:
                record, next_i = _parse_record_details(lines, i + 1)
                if record:
                    tables[current_table].append(record)
                i = next_i
                continue

        i += 1

    return ParsedDump(tables=tables)


def _coerce_value_for_column(model: Type[Any], column_name: str, value: Any) -> Any:
    """
    Convert parsed dump values to types compatible with SQLAlchemy column definitions.
    """
    if value is None:
        return None

    col = model.__table__.columns.get(column_name)  # type: ignore[attr-defined]
    if col is None:
        return value

    # Special-case enum(s)
    if model is Document and column_name == "category":
        if isinstance(value, str):
            try:
                return DocumentCategory(value)
            except Exception:
                # Fall back to raw string; DB/SQLAlchemy may still accept it depending on config.
                return value
        return value

    # Datetime
    try:
        python_type = col.type.python_type  # may raise NotImplementedError for some types
    except Exception:
        python_type = None

    # JSON / ARRAY / Enum types often don't have clean python_type; handle by name.
    type_name = col.type.__class__.__name__.lower()

    if python_type is datetime and isinstance(value, str):
        return _parse_iso_datetime(value)

    if python_type is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"true", "t", "1", "yes", "y"}:
                return True
            if v in {"false", "f", "0", "no", "n"}:
                return False
        return bool(value)

    if python_type is int:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip() != "":
            return int(value)
        return value

    if python_type is float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip() != "":
            return float(value)
        return value

    # ARRAY(String): dump stores as JSON list in details block (or "[]")
    if "array" in type_name:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed
            except Exception:
                return [value]
        return value

    # JSON columns: dump details block uses real JSON (we already json.loads) but be defensive
    if "json" in type_name:
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

    # Text/String columns that store JSON strings: if we parsed a dict/list, serialize back to JSON string
    if python_type is str or "text" in type_name or "string" in type_name:
        if isinstance(value, (dict, list)):
            # This is a Text column storing JSON, so serialize the parsed dict/list back to a string
            return json.dumps(value)
        return value

    # Strings/Text/etc. (fallback)
    return value


def _filter_to_model_columns(model: Type[Any], record: Dict[str, Any]) -> Dict[str, Any]:
    cols = {c.name for c in model.__table__.columns}  # type: ignore[attr-defined]
    out: Dict[str, Any] = {}
    for k, v in record.items():
        if k not in cols:
            continue
        out[k] = _coerce_value_for_column(model, k, v)
    return out


def _get_pk_identity(model: Type[Any], record: Dict[str, Any]) -> Optional[Any]:
    mapper = inspect(model)
    pk_cols = [c.name for c in mapper.primary_key]
    if not pk_cols:
        return None
    if any(pk not in record or record[pk] is None for pk in pk_cols):
        return None
    if len(pk_cols) == 1:
        return record[pk_cols[0]]
    return tuple(record[pk] for pk in pk_cols)


def filter_records_by_account(records: List[Dict[str, Any]], account_id: Optional[int] = None, account_email: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Filter records to only include those belonging to a specific account.
    Works by checking account_id field or email field (for ACCOUNTS table).
    """
    if account_id is None and account_email is None:
        return records
    
    filtered = []
    for record in records:
        # For ACCOUNTS table, match by email
        if account_email and "email" in record:
            if record.get("email") == account_email:
                filtered.append(record)
        # For all other tables, match by account_id
        elif account_id and "account_id" in record:
            if record.get("account_id") == account_id:
                filtered.append(record)
        # If no account_id field and not ACCOUNTS, include it (might be a table without account linkage)
        elif account_id is None and account_email:
            # We're filtering by email but this record has no email field - skip it
            continue
        else:
            # No account filtering needed for this record type
            filtered.append(record)
    
    return filtered


def upsert_records(db: Session, model: Type[Any], records: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    inserted = 0
    updated = 0

    for raw in records:
        data = _filter_to_model_columns(model, raw)
        pk_identity = _get_pk_identity(model, data)

        existing = None
        if pk_identity is not None:
            existing = db.get(model, pk_identity)

        if existing is None:
            obj = model(**data)  # type: ignore[call-arg]
            db.add(obj)
            inserted += 1
        else:
            for k, v in data.items():
                setattr(existing, k, v)
            updated += 1

    db.commit()
    return inserted, updated


def _reset_postgres_sequences(db: Session, models: Iterable[Type[Any]]) -> None:
    """
    If using PostgreSQL and tables have integer PK `id`, bump sequences to max(id)
    so future inserts don't collide.
    """
    if engine.dialect.name != "postgresql":
        return

    for model in models:
        cols = model.__table__.columns  # type: ignore[attr-defined]
        if "id" not in cols:
            continue
        id_col = cols["id"]
        try:
            if id_col.type.python_type is not int:
                continue
        except Exception:
            continue

        table_name = model.__table__.name  # type: ignore[attr-defined]
        seq = db.execute(
            text("SELECT pg_get_serial_sequence(:t, :c)"),
            {"t": table_name, "c": "id"},
        ).scalar()
        if not seq:
            continue

        max_id = db.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar()
        if max_id is None:
            continue

        # setval(seq, max_id, true)
        db.execute(text("SELECT setval(:seq, :val, true)"), {"seq": seq, "val": max_id})
        db.commit()


def create_tables_if_missing() -> None:
    # Make sure all models are imported (done above), then create schema.
    Base.metadata.create_all(bind=engine)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed database from backend/database_dump.txt")
    parser.add_argument(
        "--dump-file",
        default=str(BACKEND_DIR / "database_dump.txt"),
        help="Path to database_dump.txt (default: backend/database_dump.txt)",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create tables using SQLAlchemy metadata before seeding (safe if tables already exist).",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        default=None,
        help="Optional subset of dump TABLE names to seed (e.g., ACCOUNTS TURO_VEHICLES). Default: all.",
    )
    parser.add_argument(
        "--account-email",
        default="ibtesamnaeemdev@gmail.com",
        help="Filter to only seed data for a specific account email. Default: ibtesamnaeemdev@gmail.com (use --account-email '' to seed all accounts).",
    )
    args = parser.parse_args()

    dump_path = Path(os.path.expanduser(args.dump_file)).resolve()
    if not dump_path.exists():
        raise SystemExit(f"Dump file not found: {dump_path}")

    if args.create_tables:
        create_tables_if_missing()

    parsed = parse_database_dump(dump_path)

    # If filtering by account email, find the account_id first
    account_id = None
    if args.account_email and args.account_email.strip():
        accounts = parsed.tables.get("ACCOUNTS", [])
        matching_account = next((acc for acc in accounts if acc.get("email") == args.account_email), None)
        if matching_account:
            account_id = matching_account.get("id")
            print(f"Filtering to account: {args.account_email} (account_id={account_id})")
        else:
            raise SystemExit(f"Account with email '{args.account_email}' not found in dump file.")

    requested_tables = {t.upper() for t in args.tables} if args.tables else None
    seed_order = [
        # parents first
        "ACCOUNTS",
        "TURO_INTEGRATION",
        "BOUNCIE_TOKEN",
        "SESSION_STORAGE",
        # turo core
        "TURO_VEHICLES",
        "TURO_TRIPS",
        "TURO_REVIEWS",
        "EARNINGS_BREAKDOWN",
        "TURO_VEHICLE_EARNINGS",
        # bouncie linkage/logs
        "BOUNCIE_VEHICLE_MAPPING",
        "BOUNCIE_TRIP",
        "BOUNCIE_DTC_CODES",
        "BOUNCIE_WEBHOOK_LOGS",
        # misc
        "DOCUMENTS",
        "ACCOUNT_DELETION_LOGS",
    ]

    db = SessionLocal()
    try:
        total_inserted = 0
        total_updated = 0

        for table_name in seed_order:
            if requested_tables is not None and table_name not in requested_tables:
                continue
            model = MODEL_BY_DUMP_TABLE.get(table_name)
            if model is None:
                continue
            records = parsed.tables.get(table_name, [])
            if not records:
                continue

            # Filter by account if specified
            if args.account_email and args.account_email.strip():
                records = filter_records_by_account(records, account_id=account_id, account_email=args.account_email)
                if not records:
                    print(f"{table_name}: skipped (no records for account {args.account_email})")
                    continue

            ins, upd = upsert_records(db, model, records)
            total_inserted += ins
            total_updated += upd
            print(f"{table_name}: inserted={ins}, updated={upd}, total_records_in_dump={len(records)}")

        # Reset sequences (Postgres only) so future inserts don't collide with seeded IDs.
        _reset_postgres_sequences(db, [MODEL_BY_DUMP_TABLE[t] for t in seed_order if t in MODEL_BY_DUMP_TABLE])

        print(f"\nDone. Inserted={total_inserted}, Updated={total_updated}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())


