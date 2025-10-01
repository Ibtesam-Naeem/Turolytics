# ------------------------------ IMPORTS ------------------------------
import os
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ CONFIGURATION ------------------------------
class PlaidConfig:
    """Plaid configuration settings."""
    
    def __init__(self):
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.environment = os.getenv("PLAID_ENVIRONMENT", "sandbox")
        
        if not self.client_id or not self.secret:
            raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET environment variables are required")
        
        self._setup_client()
    
    def _setup_client(self):
        """Set up Plaid client configuration."""
        environment_map = {
            'sandbox': plaid.Environment.Sandbox,
            'development': plaid.Environment.Development,
            'production': plaid.Environment.Production
        }
        
        configuration = Configuration(
            host=environment_map.get(self.environment, plaid.Environment.Sandbox),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

# ------------------------------ PLAID CLIENT ------------------------------
class PlaidClient:
    """Client for Plaid API operations."""
    
    def __init__(self, client_id: str = None, secret: str = None, environment: str = "sandbox"):
        """Initialize Plaid client.
        
        Args:
            client_id: Plaid client ID (defaults to PLAID_CLIENT_ID env var)
            secret: Plaid secret (defaults to PLAID_SECRET env var)
            environment: Plaid environment (sandbox, development, production)
        """
        self.config = PlaidConfig()
        self.access_tokens: Dict[str, str] = {}  # Store access tokens by user_id
        logger.info(f"PlaidClient initialized for {self.config.environment} environment")
    
    def create_link_token(self, user_id: str, products: List[str] = None) -> Dict[str, Any]:
        """Create a Plaid link token for user authentication.
        
        Args:
            user_id: Unique identifier for the user
            products: List of Plaid products (defaults to ['transactions', 'auth'])
            
        Returns:
            Dictionary with link_token and metadata
        """
        try:
            if products is None:
                products = ['transactions', 'auth']
            
            logger.info(f"Creating link token for user: {user_id}")
            
            request = LinkTokenCreateRequest(
                products=[Products(p) for p in products],
                client_name="Turolytics",
                country_codes=[CountryCode('US'), CountryCode('CA')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=user_id)
            )
            
            response = self.config.client.link_token_create(request)
            
            result = {
                "success": True,
                "link_token": response['link_token'],
                "expiration": response['expiration'],
                "user_id": user_id,
                "products": products
            }
            
            logger.info(f"Link token created successfully for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating link token for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def exchange_public_token(self, public_token: str, user_id: str) -> Dict[str, Any]:
        """Exchange public token for access token.
        
        Args:
            public_token: Public token from Plaid Link
            user_id: User identifier
            
        Returns:
            Dictionary with access_token and item_id
        """
        try:
            logger.info(f"Exchanging public token for user: {user_id}")
            
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.config.client.item_public_token_exchange(request)
            
            access_token = response['access_token']
            item_id = response['item_id']
            
            # Store access token for this user
            self.access_tokens[user_id] = access_token
            
            result = {
                "success": True,
                "access_token": access_token,
                "item_id": item_id,
                "user_id": user_id
            }
            
            logger.info(f"Public token exchanged successfully for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error exchanging public token for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def get_accounts(self, user_id: str, access_token: str = None) -> Dict[str, Any]:
        """Get account information for a user.
        
        Args:
            user_id: User identifier
            access_token: Access token (if not provided, uses stored token)
            
        Returns:
            Dictionary with account information
        """
        try:
            if not access_token:
                access_token = self.access_tokens.get(user_id)
                if not access_token:
                    logger.warning(f"No access token found for user: {user_id}")
                    return {
                        "success": False,
                        "error": "No access token found for user",
                        "user_id": user_id
                    }
            
            logger.info(f"Getting accounts for user: {user_id}")
            
            request = AccountsGetRequest(access_token=access_token)
            response = self.config.client.accounts_get(request)
            
            accounts = []
            for account in response['accounts']:
                accounts.append({
                    "account_id": account['account_id'],
                    "name": account['name'],
                    "type": account['type'],
                    "subtype": account['subtype'],
                    "mask": account['mask'],
                    "available_balance": account.get('balances', {}).get('available'),
                    "current_balance": account.get('balances', {}).get('current'),
                    "iso_currency_code": account.get('balances', {}).get('iso_currency_code')
                })
            
            result = {
                "success": True,
                "accounts": accounts,
                "item_id": response['item']['item_id'],
                "user_id": user_id,
                "total_accounts": len(accounts)
            }
            
            logger.info(f"Retrieved {len(accounts)} accounts for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting accounts for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def get_transactions(self, user_id: str, start_date: str = None, end_date: str = None, 
                        count: int = 100, access_token: str = None) -> Dict[str, Any]:
        """Get transaction data for a user.
        
        Args:
            user_id: User identifier
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            count: Number of transactions to retrieve
            access_token: Access token (if not provided, uses stored token)
            
        Returns:
            Dictionary with transaction information
        """
        try:
            if not access_token:
                access_token = self.access_tokens.get(user_id)
                if not access_token:
                    logger.warning(f"No access token found for user: {user_id}")
                    return {
                        "success": False,
                        "error": "No access token found for user",
                        "user_id": user_id
                    }
            
            # Set default date range (last 30 days)
            if not start_date or not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            logger.info(f"Getting transactions for user: {user_id} ({start_date} to {end_date})")
            
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=date.fromisoformat(start_date),
                end_date=date.fromisoformat(end_date),
                options=TransactionsGetRequestOptions(count=count)
            )
            
            response = self.config.client.transactions_get(request)
            
            transactions = []
            for transaction in response['transactions']:
                transactions.append({
                    "transaction_id": transaction['transaction_id'],
                    "account_id": transaction['account_id'],
                    "amount": transaction['amount'],
                    "date": transaction['date'],
                    "name": transaction['name'],
                    "merchant_name": transaction.get('merchant_name'),
                    "category": transaction.get('category'),
                    "account_owner": transaction.get('account_owner')
                })
            
            result = {
                "success": True,
                "transactions": transactions,
                "total_transactions": response['total_transactions'],
                "user_id": user_id,
                "date_range": f"{start_date} to {end_date}"
            }
            
            logger.info(f"Retrieved {len(transactions)} transactions for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Plaid connection and credentials.
        
        Returns:
            Dictionary with connection status
        """
        try:
            logger.info("Testing Plaid connection...")
            
            # Try to create a link token as a connection test
            link_result = self.create_link_token("connection_test")
            
            if link_result["success"]:
                return {
                    "success": True,
                    "message": "Plaid connection successful",
                    "environment": self.config.environment,
                    "client_id": self.config.client_id[:8] + "..."
                }
            else:
                return {
                    "success": False,
                    "message": "Plaid connection failed",
                    "error": link_result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Plaid connection test failed: {e}")
            return {
                "success": False,
                "message": "Plaid connection failed",
                "error": str(e)
            }
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get stored information for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user information
        """
        has_access_token = user_id in self.access_tokens
        
        return {
            "user_id": user_id,
            "has_access_token": has_access_token,
            "environment": self.config.environment
        }
