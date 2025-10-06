# ------------------------------ IMPORTS ------------------------------
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Dict, List
from decimal import Decimal

from sqlalchemy.orm import Session

from core.db.base import Account, PlaidItem, PlaidAccount, PlaidTransaction, PlaidWebhookEvent
from core.db.database import get_db_session


# ------------------------------ ACCOUNT HELPERS ------------------------------

def get_or_create_account(email: str) -> Optional[int]:
    """Get or create an account by email (reuse Turo accounts table)."""
    with get_db_session() as db:
        acct = db.query(Account).filter(Account.turo_email == email).first()
        if acct:
            return acct.id
        # If not found, create
        new_acct = Account(turo_email=email, is_active=True)
        db.add(new_acct)
        db.commit()
        db.refresh(new_acct)
        return new_acct.id


# ------------------------------ ITEM UPSERT ------------------------------

def _upsert_item(db: Session, account_id: int, item_id: str, access_token: str, item_data: Dict[str, Any]) -> str:
    """Upsert a PlaidItem row."""
    existing: Optional[PlaidItem] = (
        db.query(PlaidItem)
        .filter(PlaidItem.account_id == account_id, PlaidItem.item_id == item_id)
        .first()
    )

    common_fields = dict(
        access_token=access_token,
        institution_id=item_data.get("institution_id"),
        institution_name=item_data.get("institution_name"),
        available_products=item_data.get("available_products"),
        billed_products=item_data.get("billed_products"),
        is_active=True,
        raw=item_data,
    )

    if existing:
        for k, v in common_fields.items():
            setattr(existing, k, v)
        return "updated"
    else:
        row = PlaidItem(account_id=account_id, item_id=item_id, **common_fields)
        db.add(row)
        return "created"


def save_plaid_item(account_email: str, item_id: str, access_token: str, item_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Save or update a Plaid Item."""
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {"success": False, "error": "Failed to get/create account"}

    with get_db_session() as db:
        result = _upsert_item(db, account_id, item_id, access_token, item_data or {})
        db.commit()
        return {"success": True, "result": result}


# ------------------------------ ACCOUNT UPSERT ------------------------------

def _upsert_plaid_account(db: Session, account_id: int, item_db_id: int, account_data: Dict[str, Any]) -> str:
    """Upsert a PlaidAccount row."""
    plaid_account_id = account_data.get("account_id")
    if not plaid_account_id:
        return "skipped"

    existing: Optional[PlaidAccount] = (
        db.query(PlaidAccount)
        .filter(PlaidAccount.account_id == account_id, PlaidAccount.plaid_account_id == plaid_account_id)
        .first()
    )

    balances = account_data.get("balances", {})
    
    common_fields = dict(
        item_id=item_db_id,
        name=account_data.get("name"),
        official_name=account_data.get("official_name"),
        type=account_data.get("type"),
        subtype=account_data.get("subtype"),
        mask=account_data.get("mask"),
        current_balance=Decimal(str(balances.get("current", 0))) if balances.get("current") is not None else None,
        available_balance=Decimal(str(balances.get("available", 0))) if balances.get("available") is not None else None,
        limit_amount=Decimal(str(balances.get("limit", 0))) if balances.get("limit") is not None else None,
        currency_code=balances.get("iso_currency_code"),
        is_active=True,
        last_synced_at=datetime.now(timezone.utc),
        raw=account_data,
    )

    if existing:
        for k, v in common_fields.items():
            setattr(existing, k, v)
        return "updated"
    else:
        row = PlaidAccount(account_id=account_id, plaid_account_id=plaid_account_id, **common_fields)
        db.add(row)
        return "created"


def save_plaid_accounts(account_email: str, item_id: str, accounts_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save or update Plaid accounts."""
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {"accounts_processed": 0, "created": 0, "updated": 0}

    with get_db_session() as db:
        # Get the item DB ID
        item = db.query(PlaidItem).filter(PlaidItem.account_id == account_id, PlaidItem.item_id == item_id).first()
        if not item:
            return {"accounts_processed": 0, "created": 0, "updated": 0, "error": "Item not found"}

        created = updated = processed = 0
        for acc in accounts_data:
            result = _upsert_plaid_account(db, account_id, item.id, acc)
            if result in ("created", "updated"):
                processed += 1
                if result == "created":
                    created += 1
                else:
                    updated += 1
        db.commit()
        return {"accounts_processed": processed, "created": created, "updated": updated}


# ------------------------------ TRANSACTION UPSERT ------------------------------

def _upsert_transaction(db: Session, account_id: int, plaid_account_db_id: int, txn_data: Dict[str, Any]) -> str:
    """Upsert a PlaidTransaction row."""
    transaction_id = txn_data.get("transaction_id")
    if not transaction_id:
        return "skipped"

    existing: Optional[PlaidTransaction] = (
        db.query(PlaidTransaction)
        .filter(PlaidTransaction.account_id == account_id, PlaidTransaction.transaction_id == transaction_id)
        .first()
    )

    date_str = txn_data.get("date")
    try:
        date_dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc) if date_str else None
    except Exception:
        date_dt = None

    authorized_date_str = txn_data.get("authorized_date")
    try:
        authorized_dt = datetime.fromisoformat(authorized_date_str).replace(tzinfo=timezone.utc) if authorized_date_str else None
    except Exception:
        authorized_dt = None

    common_fields = dict(
        plaid_account_id=plaid_account_db_id,
        date=date_dt,
        authorized_date=authorized_dt,
        name=txn_data.get("name"),
        merchant_name=txn_data.get("merchant_name"),
        amount=Decimal(str(txn_data.get("amount", 0))) if txn_data.get("amount") is not None else None,
        currency_code=txn_data.get("iso_currency_code"),
        category=txn_data.get("category"),
        category_id=txn_data.get("category_id"),
        pending=txn_data.get("pending", False),
        pending_transaction_id=txn_data.get("pending_transaction_id"),
        payment_channel=txn_data.get("payment_channel"),
        transaction_type=txn_data.get("transaction_type"),
        location=txn_data.get("location"),
        payment_meta=txn_data.get("payment_meta"),
        raw=txn_data,
    )

    if existing:
        for k, v in common_fields.items():
            setattr(existing, k, v)
        return "updated"
    else:
        row = PlaidTransaction(account_id=account_id, transaction_id=transaction_id, **common_fields)
        db.add(row)
        return "created"


def save_plaid_transactions(
    account_email: str, plaid_account_id: str, transactions_data: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Save or update Plaid transactions."""
    account_id = get_or_create_account(account_email)
    if not account_id:
        return {"transactions_processed": 0, "created": 0, "updated": 0}

    with get_db_session() as db:
        # Get the plaid account DB ID
        plaid_acc = (
            db.query(PlaidAccount)
            .filter(PlaidAccount.account_id == account_id, PlaidAccount.plaid_account_id == plaid_account_id)
            .first()
        )
        if not plaid_acc:
            return {"transactions_processed": 0, "created": 0, "updated": 0, "error": "Plaid account not found"}

        created = updated = processed = 0
        for txn in transactions_data:
            result = _upsert_transaction(db, account_id, plaid_acc.id, txn)
            if result in ("created", "updated"):
                processed += 1
                if result == "created":
                    created += 1
                else:
                    updated += 1
        db.commit()
        return {"transactions_processed": processed, "created": created, "updated": updated}


# ------------------------------ WEBHOOK EVENT STORAGE ------------------------------

def store_plaid_webhook_event(
    account_email: Optional[str], webhook_type: str, webhook_code: str, payload: Dict[str, Any], signature: Optional[str]
) -> int:
    """Store a Plaid webhook event for audit and optional replay."""
    account_id = get_or_create_account(account_email) if account_email else None

    item_id = payload.get("item_id")
    error = payload.get("error")
    
    with get_db_session() as db:
        evt = PlaidWebhookEvent(
            account_id=account_id,
            webhook_type=webhook_type,
            webhook_code=webhook_code,
            item_id=item_id,
            error=error,
            data=payload,
            signature=signature,
            raw_payload=payload,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)
        return evt.id

