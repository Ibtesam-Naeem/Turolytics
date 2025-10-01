# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timezone
from typing import Any, Optional, List, Dict
import logging
import traceback
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text

from ..config import SessionLocal
from ..models import Account, PlaidItem, PlaidAccount, PlaidTransaction

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ SESSION MANAGEMENT ------------------------------
@contextmanager
def get_session():
    """Context manager for database sessions with automatic commit/rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise

    finally:
        db.close()

# ------------------------------ PLAID ITEM OPERATIONS ------------------------------
def save_plaid_item(account_id: int, item_id: str, access_token: str, 
                   institution_id: str = None, institution_name: str = None) -> int:
    """Save or update Plaid item information.
    
    Args:
        account_id: Account ID
        item_id: Plaid item ID
        access_token: Plaid access token
        institution_id: Institution ID
        institution_name: Institution name
        
    Returns:
        PlaidItem ID
    """
    try:
        with get_session() as db:
            existing_item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()
            
            if existing_item:
                existing_item.access_token = access_token
                existing_item.institution_id = institution_id
                existing_item.institution_name = institution_name
                existing_item.status = "active"
                existing_item.last_successful_update = datetime.now(timezone.utc)
                existing_item.updated_at = datetime.now(timezone.utc)
                db.flush()
                return existing_item.id
            else:
                plaid_item = PlaidItem(
                    account_id=account_id,
                    item_id=item_id,
                    access_token=access_token,
                    institution_id=institution_id,
                    institution_name=institution_name,
                    status="active",
                    last_successful_update=datetime.now(timezone.utc)
                )
                db.add(plaid_item)
                db.flush()
                return plaid_item.id
                
    except Exception as e:
        logger.error(f"Error saving Plaid item: {e}")
        logger.error(traceback.format_exc())
        raise

def get_plaid_item(account_id: int, item_id: str = None) -> Optional[PlaidItem]:
    """Get Plaid item for an account.
    
    Args:
        account_id: Account ID
        item_id: Plaid item ID (optional)
        
    Returns:
        PlaidItem or None
    """
    try:
        with get_session() as db:
            if item_id:
                return db.query(PlaidItem).filter(
                    and_(PlaidItem.account_id == account_id, PlaidItem.item_id == item_id)
                ).first()
            else:
                return db.query(PlaidItem).filter(PlaidItem.account_id == account_id).first()
                
    except Exception as e:
        logger.error(f"Error getting Plaid item: {e}")
        return None

# ------------------------------ PLAID ACCOUNT OPERATIONS ------------------------------
def save_plaid_accounts(account_id: int, accounts_data: List[Dict[str, Any]]) -> int:
    """Save Plaid accounts data.
    
    Args:
        account_id: Account ID
        accounts_data: List of account data from Plaid
        
    Returns:
        Number of accounts saved
    """
    try:
        saved_count = 0
        
        with get_session() as db:
            plaid_item = get_plaid_item(account_id)
            if not plaid_item:
                logger.error(f"No Plaid item found for account {account_id}")
                return 0
            
            for account_data in accounts_data:
                try:
                    existing_account = db.query(PlaidAccount).filter(
                        and_(
                            PlaidAccount.account_id == account_id,
                            PlaidAccount.plaid_account_id == account_data['account_id']
                        )
                    ).first()
                    
                    if existing_account:
                        existing_account.name = account_data['name']
                        existing_account.type = account_data['type']
                        existing_account.subtype = account_data.get('subtype')
                        existing_account.mask = account_data.get('mask')
                        existing_account.available_balance = account_data.get('available_balance')
                        existing_account.current_balance = account_data.get('current_balance')
                        existing_account.iso_currency_code = account_data.get('iso_currency_code')
                        existing_account.updated_at = datetime.now(timezone.utc)
                    else:
                        plaid_account = PlaidAccount(
                            account_id=account_id,
                            plaid_item_id=plaid_item.id,
                            plaid_account_id=account_data['account_id'],
                            name=account_data['name'],
                            type=account_data['type'],
                            subtype=account_data.get('subtype'),
                            mask=account_data.get('mask'),
                            available_balance=account_data.get('available_balance'),
                            current_balance=account_data.get('current_balance'),
                            iso_currency_code=account_data.get('iso_currency_code')
                        )
                        db.add(plaid_account)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving account {account_data.get('account_id', 'unknown')}: {e}")
                    continue
            
            return saved_count
            
    except Exception as e:
        logger.error(f"Error saving Plaid accounts: {e}")
        logger.error(traceback.format_exc())
        raise

def get_plaid_accounts(account_id: int) -> List[PlaidAccount]:
    """Get Plaid accounts for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        List of PlaidAccount objects
    """
    try:
        with get_session() as db:
            return db.query(PlaidAccount).filter(
                PlaidAccount.account_id == account_id
            ).all()
            
    except Exception as e:
        logger.error(f"Error getting Plaid accounts: {e}")
        return []

# ------------------------------ PLAID TRANSACTION OPERATIONS ------------------------------
def save_plaid_transactions(account_id: int, transactions_data: List[Dict[str, Any]]) -> int:
    """Save Plaid transactions data.
    
    Args:
        account_id: Account ID
        transactions_data: List of transaction data from Plaid
        
    Returns:
        Number of transactions saved
    """
    try:
        saved_count = 0
        
        with get_session() as db:
            plaid_item = get_plaid_item(account_id)
            if not plaid_item:
                logger.error(f"No Plaid item found for account {account_id}")
                return 0
            
            for transaction_data in transactions_data:
                try:
                    plaid_account = db.query(PlaidAccount).filter(
                        and_(
                            PlaidAccount.account_id == account_id,
                            PlaidAccount.plaid_account_id == transaction_data['account_id']
                        )
                    ).first()
                    
                    if not plaid_account:
                        logger.warning(f"No Plaid account found for transaction {transaction_data.get('transaction_id', 'unknown')}")
                        continue
                    
                    existing_transaction = db.query(PlaidTransaction).filter(
                        PlaidTransaction.plaid_transaction_id == transaction_data['transaction_id']
                    ).first()
                    
                    if existing_transaction:
                        existing_transaction.amount = transaction_data['amount']
                        existing_transaction.name = transaction_data['name']
                        existing_transaction.merchant_name = transaction_data.get('merchant_name')
                        existing_transaction.category = transaction_data.get('category')
                        existing_transaction.account_owner = transaction_data.get('account_owner')
                        existing_transaction.updated_at = datetime.now(timezone.utc)
                    else:
                        plaid_transaction = PlaidTransaction(
                            account_id=account_id,
                            plaid_item_id=plaid_item.id,
                            plaid_account_id=plaid_account.id,
                            plaid_transaction_id=transaction_data['transaction_id'],
                            amount=transaction_data['amount'],
                            date=datetime.strptime(transaction_data['date'], '%Y-%m-%d').date(),
                            name=transaction_data['name'],
                            merchant_name=transaction_data.get('merchant_name'),
                            category=transaction_data.get('category'),
                            account_owner=transaction_data.get('account_owner')
                        )
                        db.add(plaid_transaction)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving transaction {transaction_data.get('transaction_id', 'unknown')}: {e}")
                    continue
            
            return saved_count
            
    except Exception as e:
        logger.error(f"Error saving Plaid transactions: {e}")
        logger.error(traceback.format_exc())
        raise

def get_plaid_transactions(account_id: int, start_date: str = None, end_date: str = None) -> List[PlaidTransaction]:
    """Get Plaid transactions for an account.
    
    Args:
        account_id: Account ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of PlaidTransaction objects
    """
    try:
        with get_session() as db:
            query = db.query(PlaidTransaction).filter(PlaidTransaction.account_id == account_id)
            
            if start_date:
                query = query.filter(PlaidTransaction.date >= start_date)
            if end_date:
                query = query.filter(PlaidTransaction.date <= end_date)
            
            return query.order_by(desc(PlaidTransaction.date)).all()
            
    except Exception as e:
        logger.error(f"Error getting Plaid transactions: {e}")
        return []

# ------------------------------ COMBINED OPERATIONS ------------------------------
def get_plaid_data(account_id: int) -> Dict[str, Any]:
    """Get all Plaid data for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Dictionary with all Plaid data
    """
    try:
        with get_session() as db:
            plaid_item = get_plaid_item(account_id)
            
            accounts = get_plaid_accounts(account_id)
            
            transactions = get_plaid_transactions(account_id)
            
            return {
                "success": True,
                "plaid_item": plaid_item.to_dict() if plaid_item else None,
                "accounts": [account.to_dict() for account in accounts],
                "transactions": [transaction.to_dict() for transaction in transactions],
                "account_count": len(accounts),
                "transaction_count": len(transactions)
            }
            
    except Exception as e:
        logger.error(f"Error getting Plaid data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def delete_plaid_data(account_id: int) -> bool:
    """Delete all Plaid data for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        True if successful
    """
    try:
        with get_session() as db:
            # Delete transactions
            db.query(PlaidTransaction).filter(PlaidTransaction.account_id == account_id).delete()
            
            # Delete accounts
            db.query(PlaidAccount).filter(PlaidAccount.account_id == account_id).delete()
            
            # Delete items
            db.query(PlaidItem).filter(PlaidItem.account_id == account_id).delete()
            
            return True
            
    except Exception as e:
        logger.error(f"Error deleting Plaid data: {e}")
        return False
