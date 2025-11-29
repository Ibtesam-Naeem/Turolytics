# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .service import PlaidService
from .transaction_filter import filter_vehicle_transactions, categorize_all_transactions
from .schemas import (
    APIResponse,
    LinkTokenRequest,
    PublicTokenExchangeRequest,
    TransactionSyncRequest,
    TransactionGetRequest,
    AccountToggleRequest,
    TransactionLinkReceiptRequest,
    PlaidIntegrationOut,
    PlaidAccountOut,
    TransactionOut,
    TransactionDetailOut,
)
from core.database import get_db
from core.database.models import (
    Account,
    PlaidIntegration,
    PlaidAccount,
    Transaction,
    Document,
)
from core.database.db_service import DatabaseService

logger = logging.getLogger(__name__)

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_plaid_service(
    db: Session = Depends(get_db),
    account_id: Optional[int] = Query(None, description="Account ID")
) -> PlaidService:
    return PlaidService(db=db, account_id=account_id)

def get_account_or_raise(db: Session, account_id: int) -> Account:
    """Get account by ID or user_id, raise HTTPException if not found."""
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        account = DatabaseService.get_account_by_user_id(db, account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    return account

# ------------------------------ HELPER FUNCTIONS ------------------------------

def check_result(result: Dict[str, Any], operation: str) -> APIResponse:
    """Check service result and raise exception if failed."""
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Plaid {operation} failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Plaid {operation} failed: {error_msg}")
    return APIResponse(success=True, data=result.get("data", {}))

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.post("/auth/link-token", response_model=APIResponse, tags=["Authentication"])
async def create_link_token(
    request: LinkTokenRequest,
    service: PlaidService = Depends(get_plaid_service)
):
    """
    Create a Plaid Link token for initializing Plaid Link.
    The frontend uses this token to open Plaid Link.
    """
    if service.account_id != request.account_id:
        service.account_id = request.account_id
    
    result = await service.create_link_token(user_id=request.user_id)
    return check_result(result, "create link token")

@router.post("/auth/token", response_model=APIResponse, tags=["Authentication"])
async def exchange_public_token(
    request: PublicTokenExchangeRequest,
    db: Session = Depends(get_db),
    service: PlaidService = Depends(get_plaid_service)
):
    """
    Exchange public token from Plaid Link for access token.
    This is called after user successfully links their bank account.
    """
    if service.account_id != request.account_id:
        service.account_id = request.account_id
    
    result = await service.exchange_public_token(request.public_token)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Token exchange failed"))
    
    # Fetch and store accounts
    access_token = result["data"]["access_token"]
    accounts_result = await service.get_accounts(access_token)
    
    if accounts_result.get("success"):
        await _store_accounts(db, request.account_id, accounts_result["data"], service.item_id)
    
    return APIResponse(success=True, data=result["data"])

# ------------------------------ INTEGRATION ROUTES ------------------------------

@router.get("/integration", response_model=APIResponse, tags=["Integration"])
async def get_integration(
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get Plaid integration status for an account."""
    account = get_account_or_raise(db, account_id)
    
    integration = db.query(PlaidIntegration).filter(
        PlaidIntegration.account_id == account.id
    ).first()
    
    if not integration:
        return APIResponse(success=True, data={"integration": None})
    
    return APIResponse(
        success=True,
        data={"integration": PlaidIntegrationOut.model_validate(integration, from_attributes=True).model_dump()}
    )

@router.delete("/integration", response_model=APIResponse, tags=["Integration"])
async def delete_integration(
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Delete Plaid integration and all associated data."""
    account = get_account_or_raise(db, account_id)
    
    integration = db.query(PlaidIntegration).filter(
        PlaidIntegration.account_id == account.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Plaid integration not found")
    
    db.delete(integration)
    db.commit()
    
    return APIResponse(success=True, data={"message": "Plaid integration deleted successfully"})

# ------------------------------ ACCOUNT ROUTES ------------------------------

@router.get("/accounts", response_model=APIResponse, tags=["Accounts"])
async def get_accounts(
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    service: PlaidService = Depends(get_plaid_service)
):
    """Get linked bank accounts from Plaid."""
    account = get_account_or_raise(db, account_id)
    
    if service.account_id != account_id:
        service.account_id = account_id
        service._load_tokens()
    
    if not service.access_token:
        raise HTTPException(status_code=401, detail="Plaid integration not found. Please link your bank account first.")
    
    result = await service.get_accounts()
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to fetch accounts"))
    
    # Also return stored accounts from database
    stored_accounts = db.query(PlaidAccount).filter(
        PlaidAccount.account_id == account.id
    ).all()
    
    return APIResponse(
        success=True,
        data={
            "plaid_accounts": result["data"],
            "stored_accounts": [
                PlaidAccountOut.model_validate(acc, from_attributes=True).model_dump()
                for acc in stored_accounts
            ]
        }
    )

@router.get("/accounts/stored", response_model=APIResponse, tags=["Accounts"])
async def get_stored_accounts(
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get stored bank accounts from database."""
    account = get_account_or_raise(db, account_id)
    
    accounts = db.query(PlaidAccount).filter(
        PlaidAccount.account_id == account.id
    ).all()
    
    return APIResponse(
        success=True,
        data={
            "accounts": [
                PlaidAccountOut.model_validate(acc, from_attributes=True).model_dump()
                for acc in accounts
            ]
        }
    )

@router.post("/accounts/{plaid_account_id}/toggle", response_model=APIResponse, tags=["Accounts"])
async def toggle_account(
    plaid_account_id: int = Path(..., description="PlaidAccount ID"),
    request: AccountToggleRequest = ...,
    db: Session = Depends(get_db)
):
    """Toggle account monitoring (enable/disable transaction syncing)."""
    account = get_account_or_raise(db, request.account_id)
    
    plaid_account = db.query(PlaidAccount).filter(
        PlaidAccount.id == plaid_account_id,
        PlaidAccount.account_id == account.id
    ).first()
    
    if not plaid_account:
        raise HTTPException(status_code=404, detail="Plaid account not found")
    
    plaid_account.is_active = request.is_active
    db.commit()
    db.refresh(plaid_account)
    
    return APIResponse(
        success=True,
        data={"account": PlaidAccountOut.model_validate(plaid_account, from_attributes=True).model_dump()}
    )

# ------------------------------ TRANSACTION ROUTES ------------------------------

@router.post("/transactions/sync", response_model=APIResponse, tags=["Transactions"])
async def sync_transactions(
    request: TransactionSyncRequest,
    db: Session = Depends(get_db),
    service: PlaidService = Depends(get_plaid_service)
):
    """
    Sync transactions from Plaid.
    Fetches new/updated transactions and stores them in database.
    """
    account = get_account_or_raise(db, request.account_id)
    
    if service.account_id != request.account_id:
        service.account_id = request.account_id
        service._load_tokens()
    
    if not service.access_token:
        raise HTTPException(status_code=401, detail="Plaid integration not found")
    
    integration = db.query(PlaidIntegration).filter(
        PlaidIntegration.account_id == account.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Plaid integration not found")
    
    # Get cursor from integration or request
    cursor = request.cursor or integration.cursor
    
    # Sync transactions
    result = await service.sync_transactions(cursor=cursor)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Sync failed"))
    
    transactions_data = result["data"]["transactions"]
    next_cursor = result["data"].get("next_cursor")
    has_more = result["data"].get("has_more", False)
    
    # Store transactions
    stored_count = await _store_transactions(db, account.id, transactions_data, service)
    
    # Update integration cursor
    if next_cursor:
        integration.cursor = next_cursor
        integration.last_sync_at = datetime.now()
        db.commit()
    
    return APIResponse(
        success=True,
        data={
            "synced_count": stored_count,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "message": f"Synced {stored_count} transactions"
        }
    )

@router.get("/transactions", response_model=APIResponse, tags=["Transactions"])
async def get_transactions(
    account_id: int = Query(..., description="Account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vehicle_related_only: bool = Query(False, description="Filter to vehicle-related only"),
    transaction_type: Optional[str] = Query(None, description="Filter by type: 'expense' or 'revenue'"),
    vehicle_category: Optional[str] = Query(None, description="Filter by vehicle category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    include_details: bool = Query(False, description="Include full transaction details"),
    db: Session = Depends(get_db)
):
    """Get transactions from database with filtering."""
    account = get_account_or_raise(db, account_id)
    
    query = db.query(Transaction).filter(Transaction.account_id == account.id)
    
    # Date filtering
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Transaction.date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Transaction.date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    # Vehicle-related filtering
    if vehicle_related_only:
        query = query.filter(Transaction.is_vehicle_related == True)
    
    # Transaction type filtering
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    # Vehicle category filtering
    if vehicle_category:
        query = query.filter(Transaction.vehicle_category == vehicle_category)
    
    total = query.count()
    
    transactions = query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()
    
    if include_details:
        transactions_data = [
            TransactionDetailOut.model_validate(t, from_attributes=True).model_dump()
            for t in transactions
        ]
    else:
        transactions_data = [
            TransactionOut.model_validate(t, from_attributes=True).model_dump()
            for t in transactions
        ]
    
    return APIResponse(
        success=True,
        data={
            "transactions": transactions_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/transactions/{transaction_id}", response_model=APIResponse, tags=["Transactions"])
async def get_transaction(
    transaction_id: int = Path(..., description="Transaction ID"),
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get specific transaction by ID."""
    account = get_account_or_raise(db, account_id)
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.account_id == account.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return APIResponse(
        success=True,
        data={"transaction": TransactionDetailOut.model_validate(transaction, from_attributes=True).model_dump()}
    )

@router.get("/transactions/expenses", response_model=APIResponse, tags=["Transactions"])
async def get_expenses(
    account_id: int = Query(..., description="Account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vehicle_category: Optional[str] = Query(None, description="Filter by vehicle category"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get vehicle-related expenses."""
    return await get_transactions(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        vehicle_related_only=True,
        transaction_type="expense",
        vehicle_category=vehicle_category,
        limit=limit,
        offset=offset,
        db=db
    )

@router.get("/transactions/revenue", response_model=APIResponse, tags=["Transactions"])
async def get_revenue(
    account_id: int = Query(..., description="Account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get revenue transactions."""
    return await get_transactions(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        vehicle_related_only=False,
        transaction_type="revenue",
        limit=limit,
        offset=offset,
        db=db
    )

@router.post("/transactions/{transaction_id}/link-receipt", response_model=APIResponse, tags=["Transactions"])
async def link_transaction_receipt(
    transaction_id: int = Path(..., description="Transaction ID"),
    request: TransactionLinkReceiptRequest = ...,
    db: Session = Depends(get_db)
):
    """Link a transaction to a receipt/document."""
    account = get_account_or_raise(db, request.account_id)
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.account_id == account.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.account_id == account.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    transaction.document_id = request.document_id
    db.commit()
    db.refresh(transaction)
    
    return APIResponse(
        success=True,
        data={
            "message": "Transaction linked to receipt successfully",
            "transaction": TransactionOut.model_validate(transaction, from_attributes=True).model_dump()
        }
    )

# ------------------------------ RECEIPT VERIFICATION ROUTES ------------------------------

@router.get("/receipts/{document_id}/verify-transaction", response_model=APIResponse, tags=["Receipts"])
async def verify_receipt_transaction(
    document_id: int = Path(..., description="Document ID"),
    account_id: int = Query(..., description="Account ID"),
    date_window: int = Query(3, ge=1, le=30, description="Date window in days (±days from receipt date)"),
    db: Session = Depends(get_db)
):
    """
    Find matching transactions for a receipt.
    Returns candidate transactions with match scores.
    """
    from core.database.models.s3 import Document
    from datetime import timedelta
    
    account = get_account_or_raise(db, account_id)
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == account.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Calculate date range
    receipt_date = document.created_at
    start_date = receipt_date - timedelta(days=date_window)
    end_date = receipt_date + timedelta(days=date_window)
    
    # Map document category to transaction category
    category_mapping = {
        "gas_receipt": "gas",
        "insurance": "insurance",
        "repair": "repair",
        "maintenance": "maintenance",
        "parking_ticket": "parking",
        "toll_booth": "toll",
        "registration": "registration",
    }
    
    vehicle_category = category_mapping.get(document.category.value, None)
    
    # Query transactions in date range
    query = db.query(Transaction).filter(
        Transaction.account_id == account.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    
    # Filter by vehicle category if applicable
    if vehicle_category:
        query = query.filter(Transaction.vehicle_category == vehicle_category)
    
    transactions = query.order_by(Transaction.date.desc()).limit(10).all()
    
    # Score each transaction
    candidates = []
    for transaction in transactions:
        score = _calculate_receipt_match_score(document, transaction, receipt_date)
        if score > 0.3:  # Threshold
            candidates.append({
                "transaction": TransactionOut.model_validate(transaction, from_attributes=True).model_dump(),
                "match_score": float(score),
                "match_reasons": _get_match_reasons(document, transaction, receipt_date, score)
            })
    
    # Sort by score
    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    return APIResponse(
        success=True,
        data={
            "document": {
                "id": document.id,
                "file_name": document.file_name,
                "category": document.category.value,
                "created_at": document.created_at.isoformat() if document.created_at else None,
            },
            "candidates": candidates,
            "best_match": candidates[0] if candidates else None
        }
    )

def _calculate_receipt_match_score(document, transaction, receipt_date) -> float:
    """Calculate match score between receipt and transaction (0.0-1.0)."""
    score = 0.0
    reasons = []
    
    # Date matching (0.4 weight)
    date_diff = abs((transaction.date - receipt_date).days)
    if date_diff == 0:
        date_score = 1.0
    elif date_diff == 1:
        date_score = 0.8
    elif date_diff == 2:
        date_score = 0.6
    else:
        date_score = max(0.0, 1.0 - (date_diff * 0.1))
    
    score += date_score * 0.4
    
    # Category matching (0.3 weight)
    category_mapping = {
        "gas_receipt": "gas",
        "insurance": "insurance",
        "repair": "repair",
        "maintenance": "maintenance",
        "parking_ticket": "parking",
        "toll_booth": "toll",
        "registration": "registration",
    }
    
    doc_category = category_mapping.get(document.category.value, None)
    if doc_category and transaction.vehicle_category == doc_category:
        score += 0.3
    
    # Vehicle-related flag (0.3 weight)
    if transaction.is_vehicle_related:
        score += 0.3
    
    return min(1.0, score)

def _get_match_reasons(document, transaction, receipt_date, score) -> List[str]:
    """Get list of reasons why transaction matches receipt."""
    reasons = []
    
    # Date match
    date_diff = abs((transaction.date - receipt_date).days)
    if date_diff == 0:
        reasons.append("Date matches exactly")
    elif date_diff <= 2:
        reasons.append(f"Date within {date_diff} day(s)")
    
    # Category match
    category_mapping = {
        "gas_receipt": "gas",
        "insurance": "insurance",
        "repair": "repair",
        "maintenance": "maintenance",
        "parking_ticket": "parking",
        "toll_booth": "toll",
        "registration": "registration",
    }
    
    doc_category = category_mapping.get(document.category.value, None)
    if doc_category and transaction.vehicle_category == doc_category:
        reasons.append(f"Category matches ({doc_category})")
    
    # Vehicle-related
    if transaction.is_vehicle_related:
        reasons.append("Vehicle-related transaction")
    
    # High confidence
    if score >= 0.8:
        reasons.append("High confidence match")
    elif score >= 0.5:
        reasons.append("Medium confidence match")
    
    return reasons

# ------------------------------ ANALYTICS ROUTES ------------------------------

@router.get("/analytics/summary", response_model=APIResponse, tags=["Analytics"])
async def get_analytics_summary(
    account_id: int = Query(..., description="Account ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get expense/revenue summary."""
    account = get_account_or_raise(db, account_id)
    
    query = db.query(Transaction).filter(Transaction.account_id == account.id)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Transaction.date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Transaction.date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    # Calculate totals
    from sqlalchemy import func
    
    expenses = query.filter(
        Transaction.is_vehicle_related == True,
        Transaction.transaction_type == "expense"
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    revenue = query.filter(
        Transaction.transaction_type == "revenue"
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Count by category
    category_counts = db.query(
        Transaction.vehicle_category,
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.amount).label("total")
    ).filter(
        Transaction.account_id == account.id,
        Transaction.is_vehicle_related == True,
        Transaction.transaction_type == "expense"
    )
    
    if start_date:
        category_counts = category_counts.filter(Transaction.date >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        category_counts = category_counts.filter(Transaction.date <= datetime.strptime(end_date, "%Y-%m-%d"))
    
    category_counts = category_counts.group_by(Transaction.vehicle_category).all()
    
    return APIResponse(
        success=True,
        data={
            "total_expenses": float(expenses),
            "total_revenue": float(revenue),
            "net": float(revenue + expenses),  # expenses are negative
            "by_category": [
                {
                    "category": cat,
                    "count": count,
                    "total": float(total)
                }
                for cat, count, total in category_counts
            ]
        }
    )

# ------------------------------ HELPER FUNCTIONS ------------------------------

async def _store_accounts(
    db: Session,
    account_id: int,
    accounts_data: List[Dict[str, Any]],
    item_id: str
):
    """Store Plaid accounts in database."""
    account = get_account_or_raise(db, account_id)
    
    integration = db.query(PlaidIntegration).filter(
        PlaidIntegration.account_id == account.id
    ).first()
    
    if not integration:
        logger.error(f"Integration not found for account {account_id}")
        return
    
    for acc_data in accounts_data:
        plaid_account = db.query(PlaidAccount).filter(
            PlaidAccount.plaid_account_id == acc_data["account_id"]
        ).first()
        
        if not plaid_account:
            plaid_account = PlaidAccount(
                plaid_integration_id=integration.id,
                account_id=account.id,
                plaid_account_id=acc_data["account_id"],
                name=acc_data["name"],
                official_name=acc_data.get("official_name"),
                type=acc_data["type"],
                subtype=acc_data.get("subtype"),
                mask=acc_data.get("mask"),
                balance_current=str(acc_data["balances"].get("current")) if acc_data["balances"].get("current") else None,
                balance_available=str(acc_data["balances"].get("available")) if acc_data["balances"].get("available") else None,
                balance_limit=str(acc_data["balances"].get("limit")) if acc_data["balances"].get("limit") else None,
            )
            db.add(plaid_account)
        else:
            # Update existing account
            plaid_account.name = acc_data["name"]
            plaid_account.official_name = acc_data.get("official_name")
            plaid_account.balance_current = str(acc_data["balances"].get("current")) if acc_data["balances"].get("current") else None
            plaid_account.balance_available = str(acc_data["balances"].get("available")) if acc_data["balances"].get("available") else None
            plaid_account.balance_limit = str(acc_data["balances"].get("limit")) if acc_data["balances"].get("limit") else None
    
    db.commit()

async def _store_transactions(
    db: Session,
    account_id: int,
    transactions_data: List[Dict[str, Any]],
    service: PlaidService
) -> int:
    """Store transactions in database with filtering and categorization."""
    from .transaction_filter import categorize_all_transactions
    from .helpers import parse_plaid_date
    from decimal import Decimal
    
    account = get_account_or_raise(db, account_id)
    
    # Categorize transactions
    categorized = categorize_all_transactions(transactions_data)
    
    stored_count = 0
    
    for trans_data in categorized:
        # Get PlaidAccount
        plaid_account = db.query(PlaidAccount).filter(
            PlaidAccount.plaid_account_id == trans_data["account_id"],
            PlaidAccount.account_id == account.id
        ).first()
        
        if not plaid_account:
            logger.warning(f"PlaidAccount not found for account_id {trans_data['account_id']}")
            continue
        
        # Check if transaction already exists
        existing = db.query(Transaction).filter(
            Transaction.plaid_transaction_id == trans_data["transaction_id"]
        ).first()
        
        trans_date = parse_plaid_date(trans_data["date"])
        if not trans_date:
            logger.warning(f"Invalid date for transaction {trans_data['transaction_id']}")
            continue
        
        if existing:
            # Update existing transaction
            existing.amount = Decimal(str(trans_data["amount"]))
            existing.merchant_name = trans_data.get("merchant_name")
            existing.name = trans_data["name"]
            existing.category_primary = trans_data.get("primary_category")
            existing.category_detailed = trans_data.get("detailed_category")
            existing.plaid_category = trans_data.get("category")
            existing.is_vehicle_related = trans_data.get("is_vehicle_related", False)
            existing.vehicle_category = trans_data.get("vehicle_category")
            existing.transaction_type = trans_data.get("transaction_type")
            existing.match_confidence = Decimal(str(trans_data.get("match_confidence", 0.0)))
        else:
            # Create new transaction
            transaction = Transaction(
                account_id=account.id,
                plaid_account_id=plaid_account.id,
                plaid_transaction_id=trans_data["transaction_id"],
                date=trans_date,
                amount=Decimal(str(trans_data["amount"])),
                merchant_name=trans_data.get("merchant_name"),
                name=trans_data["name"],
                category_primary=trans_data.get("primary_category"),
                category_detailed=trans_data.get("detailed_category"),
                plaid_category=trans_data.get("category"),
                is_vehicle_related=trans_data.get("is_vehicle_related", False),
                vehicle_category=trans_data.get("vehicle_category"),
                transaction_type=trans_data.get("transaction_type"),
                match_confidence=Decimal(str(trans_data.get("match_confidence", 0.0))),
                plaid_data=trans_data
            )
            db.add(transaction)
            stored_count += 1
    
    db.commit()
    return stored_count

# ------------------------------ END OF FILE ------------------------------

