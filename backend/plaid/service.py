# ------------------------------ IMPORTS ------------------------------
import asyncio
import logging
import os
import plaid
from plaid.api import plaid_api
from plaid.model import (
    CountryCode,
    Products,
    LinkTokenCreateRequest,
    LinkTokenCreateRequestUser,
    ItemPublicTokenExchangeRequest,
    AccountsGetRequest,
    TransactionsGetRequest,
    TransactionsSyncRequest,
)
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .helpers import format_date_for_api, parse_plaid_date
from core.database.models import PlaidIntegration, PlaidAccount, Account, Transaction
from core.database.db_service import DatabaseService

load_dotenv()

logger = logging.getLogger(__name__)

# ------------------------------ PLAID CONFIGURATION ------------------------------

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")  # sandbox, development, production

# Plaid environment mapping
PLAID_ENVIRONMENTS = {
    "sandbox": plaid.Environment.sandbox,
    "development": plaid.Environment.development,
    "production": plaid.Environment.production,
}

# ------------------------------ PLAID SERVICE ------------------------------

class PlaidService:
    def __init__(
        self,
        db: Session = None,
        account_id: int = None,
        client_id: str = None,
        secret: str = None
    ):
        self.client_id = client_id or PLAID_CLIENT_ID
        self.secret = secret or PLAID_SECRET
        self.env = PLAID_ENVIRONMENTS.get(PLAID_ENV, plaid.Environment.sandbox)
        
        self.db = db
        self.account_id = account_id
        
        self.access_token = None
        self.item_id = None
        
        # Initialize Plaid client
        configuration = Configuration(
            host=self.env,
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        if self.db and self.account_id:
            self._load_tokens()

    # ------------------------------ TOKEN MANAGEMENT ------------------------------

    def _load_tokens(self):
        """Load tokens from database for the current account."""
        if not self.db or not self.account_id:
            return

        try:
            account = self.db.query(Account).filter(Account.id == self.account_id).first()
            
            if not account:
                account = DatabaseService.get_account_by_user_id(self.db, self.account_id)
            
            if not account:
                logger.warning(f"Account {self.account_id} not found")
                return
            
            integration = self.db.query(PlaidIntegration).filter(
                PlaidIntegration.account_id == account.id
            ).first()
            
            if integration:
                self.access_token = integration.access_token
                self.item_id = integration.item_id
                logger.debug(f"Loaded Plaid tokens for account {account.id} (user_id: {account.user_id})")
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")

    def _save_tokens(
        self,
        access_token: str,
        item_id: str,
        institution_id: Optional[str] = None,
        institution_name: Optional[str] = None
    ):
        """Save or update tokens in the database."""
        if not self.db or not self.account_id:
            logger.warning("Cannot save tokens: No DB session or account_id provided")
            return False

        try:
            account = self.db.query(Account).filter(Account.id == self.account_id).first()
            
            if not account:
                account = DatabaseService.get_account_by_user_id(self.db, self.account_id)
            
            if not account:
                logger.error(f"Account {self.account_id} not found - cannot save tokens")
                return False
            
            integration = self.db.query(PlaidIntegration).filter(
                PlaidIntegration.account_id == account.id
            ).first()
            
            if not integration:
                integration = PlaidIntegration(account_id=account.id)
                self.db.add(integration)
            
            integration.access_token = access_token
            integration.item_id = item_id
            if institution_id:
                integration.institution_id = institution_id
            if institution_name:
                integration.institution_name = institution_name
            
            self.db.commit()
            self.db.refresh(integration)
            
            self.access_token = access_token
            self.item_id = item_id
            
            logger.info(f"Saved Plaid tokens for account {account.id} (user_id: {account.user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tokens: {e}", exc_info=True)
            self.db.rollback()
            return False

    # ------------------------------ AUTHENTICATION ------------------------------
    
    async def create_link_token(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a Link token for Plaid Link initialization."""
        try:
            user = LinkTokenCreateRequestUser(client_user_id=user_id or str(self.account_id or "user"))
            
            request = LinkTokenCreateRequest(
                products=[Products("transactions")],
                client_name="Turolytics",
                country_codes=[CountryCode("US")],
                language="en",
                user=user,
            )
            
            response = await asyncio.to_thread(
                self.client.link_token_create,
                request
            )
            
            return {
                "success": True,
                "data": {
                    "link_token": response.link_token,
                    "expiration": response.expiration if hasattr(response, 'expiration') else None
                }
            }
        except Exception as e:
            logger.error(f"Error creating link token: {e}")
            return {"success": False, "error": str(e)}
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token."""
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = await asyncio.to_thread(
                self.client.item_public_token_exchange,
                request
            )
            
            access_token = response.access_token
            item_id = response.item_id
            
            # Get institution info
            institution_info = await self.get_institution_info(access_token)
            institution_id = institution_info.get("institution_id")
            institution_name = institution_info.get("institution_name")
            
            if self.db and self.account_id:
                save_success = self._save_tokens(
                    access_token,
                    item_id,
                    institution_id=institution_id,
                    institution_name=institution_name
                )
                if not save_success:
                    logger.warning("Token exchange succeeded but failed to save to database")
            else:
                self.access_token = access_token
                self.item_id = item_id

            return {
                "success": True,
                "data": {
                    "access_token": access_token,
                    "item_id": item_id,
                    "institution_id": institution_id,
                    "institution_name": institution_name
                }
            }
        except Exception as e:
            logger.error(f"Error exchanging public token: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_institution_info(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Get institution information for the linked item."""
        try:
            token = access_token or self.access_token
            if not token:
                return {"institution_id": None, "institution_name": None}
            
            # Note: Plaid doesn't have a direct endpoint for this in the Python SDK
            # We'll get it from accounts or item endpoint
            accounts_result = await self.get_accounts(token)
            if accounts_result.get("success") and accounts_result.get("data"):
                # Institution info might be in account data
                return {
                    "institution_id": None,  # Would need item endpoint
                    "institution_name": None
                }
            return {"institution_id": None, "institution_name": None}
        except Exception as e:
            logger.error(f"Error getting institution info: {e}")
            return {"institution_id": None, "institution_name": None}
    
    # ------------------------------ CORE API METHODS ------------------------------
    
    async def get_accounts(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Get accounts for the linked item."""
        try:
            token = access_token or self.access_token
            if not token:
                return {"success": False, "error": "No access token available"}
            
            request = AccountsGetRequest(access_token=token)
            response = await asyncio.to_thread(
                self.client.accounts_get,
                request
            )
            
            accounts = []
            for account in response["accounts"]:
                accounts.append({
                    "account_id": account.account_id,
                    "name": account.name,
                    "official_name": account.official_name if hasattr(account, 'official_name') else None,
                    "type": account.type.value if hasattr(account.type, 'value') else str(account.type),
                    "subtype": account.subtype.value if hasattr(account.subtype, 'value') and account.subtype else None,
                    "mask": account.mask if hasattr(account, 'mask') else None,
                    "balances": {
                        "current": account.balances.current if hasattr(account.balances, 'current') else None,
                        "available": account.balances.available if hasattr(account.balances, 'available') else None,
                        "limit": account.balances.limit if hasattr(account.balances, 'limit') else None,
                    }
                })
            
            return {"success": True, "data": accounts}
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transactions for the linked item."""
        try:
            token = access_token or self.access_token
            if not token:
                return {"success": False, "error": "No access token available"}
            
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            request = TransactionsGetRequest(
                access_token=token,
                start_date=format_date_for_api(start_date),
                end_date=format_date_for_api(end_date),
                account_ids=account_ids
            )
            
            response = await asyncio.to_thread(
                self.client.transactions_get,
                request
            )
            
            transactions = []
            for transaction in response["transactions"]:
                category_list = transaction.category if hasattr(transaction, 'category') and transaction.category else []
                transactions.append({
                    "transaction_id": transaction.transaction_id,
                    "account_id": transaction.account_id,
                    "amount": float(transaction.amount) if hasattr(transaction, 'amount') else 0.0,
                    "date": str(transaction.date) if hasattr(transaction, 'date') else None,
                    "name": transaction.name if hasattr(transaction, 'name') else "",
                    "merchant_name": transaction.merchant_name if hasattr(transaction, 'merchant_name') and transaction.merchant_name else None,
                    "category": category_list,
                    "category_id": transaction.category_id if hasattr(transaction, 'category_id') and transaction.category_id else None,
                    "primary_category": category_list[0] if category_list else None,
                    "detailed_category": category_list[-1] if category_list else None,
                    "pending": transaction.pending if hasattr(transaction, 'pending') else False,
                    "iso_currency_code": transaction.iso_currency_code if hasattr(transaction, 'iso_currency_code') and transaction.iso_currency_code else None,
                    "unofficial_currency_code": transaction.unofficial_currency_code if hasattr(transaction, 'unofficial_currency_code') and transaction.unofficial_currency_code else None,
                })
            
            return {
                "success": True,
                "data": {
                    "transactions": transactions,
                    "total_transactions": response.get("total_transactions", len(transactions))
                }
            }
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_transactions(
        self,
        cursor: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync transactions using cursor-based pagination."""
        try:
            token = access_token or self.access_token
            if not token:
                return {"success": False, "error": "No access token available"}
            
            request = TransactionsSyncRequest(
                access_token=token,
                cursor=cursor
            )
            
            response = await asyncio.to_thread(
                self.client.transactions_sync,
                request
            )
            
            transactions = []
            added_transactions = response.added if hasattr(response, 'added') else []
            for transaction in added_transactions:
                category_list = transaction.category if hasattr(transaction, 'category') and transaction.category else []
                transactions.append({
                    "transaction_id": transaction.transaction_id,
                    "account_id": transaction.account_id,
                    "amount": float(transaction.amount) if hasattr(transaction, 'amount') else 0.0,
                    "date": str(transaction.date) if hasattr(transaction, 'date') else None,
                    "name": transaction.name if hasattr(transaction, 'name') else "",
                    "merchant_name": transaction.merchant_name if hasattr(transaction, 'merchant_name') and transaction.merchant_name else None,
                    "category": category_list,
                    "category_id": transaction.category_id if hasattr(transaction, 'category_id') and transaction.category_id else None,
                    "primary_category": category_list[0] if category_list else None,
                    "detailed_category": category_list[-1] if category_list else None,
                    "pending": transaction.pending if hasattr(transaction, 'pending') else False,
                    "iso_currency_code": transaction.iso_currency_code if hasattr(transaction, 'iso_currency_code') and transaction.iso_currency_code else None,
                    "unofficial_currency_code": transaction.unofficial_currency_code if hasattr(transaction, 'unofficial_currency_code') and transaction.unofficial_currency_code else None,
                })
            
            return {
                "success": True,
                "data": {
                    "transactions": transactions,
                    "next_cursor": response.next_cursor if hasattr(response, 'next_cursor') else None,
                    "has_more": response.has_more if hasattr(response, 'has_more') else False
                }
            }
        except Exception as e:
            logger.error(f"Error syncing transactions: {e}")
            return {"success": False, "error": str(e)}

# ------------------------------ END OF FILE ------------------------------

