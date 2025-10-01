# ------------------------------ IMPORTS ------------------------------
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .client import PlaidClient
from database.operations.plaid import save_plaid_accounts, save_plaid_transactions, get_plaid_data

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ PLAID SERVICE ------------------------------
class PlaidService:
    """Service for handling Plaid business logic and data operations."""
    
    def __init__(self):
        """Initialize Plaid service."""
        self.client = PlaidClient()
        logger.info("PlaidService initialized")
    
    def create_link_token(self, user_id: str, products: List[str] = None) -> Dict[str, Any]:
        """Create a Plaid link token for user authentication.
        
        Args:
            user_id: Unique identifier for the user
            products: List of Plaid products (defaults to ['transactions', 'auth'])
            
        Returns:
            Dictionary with link_token and metadata
        """
        try:
            logger.info(f"Creating link token for user: {user_id}")
            result = self.client.create_link_token(user_id, products)
            
            if result["success"]:
                logger.info(f"Link token created successfully for user: {user_id}")
            else:
                logger.error(f"Failed to create link token for user {user_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in PlaidService.create_link_token for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def exchange_public_token(self, public_token: str, user_id: str) -> Dict[str, Any]:
        """Exchange public token for access token and save to database.
        
        Args:
            public_token: Public token from Plaid Link
            user_id: User identifier
            
        Returns:
            Dictionary with access_token and item_id
        """
        try:
            logger.info(f"Exchanging public token for user: {user_id}")
            result = self.client.exchange_public_token(public_token, user_id)
            
            if result["success"]:
                logger.info(f"Public token exchanged successfully for user: {user_id}")
                # TODO: Save access token to database
                # save_plaid_access_token(user_id, result["access_token"], result["item_id"])
            else:
                logger.error(f"Failed to exchange public token for user {user_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in PlaidService.exchange_public_token for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def get_and_save_accounts(self, user_id: str, access_token: str = None) -> Dict[str, Any]:
        """Get account information and save to database.
        
        Args:
            user_id: User identifier
            access_token: Access token (if not provided, uses stored token)
            
        Returns:
            Dictionary with account information
        """
        try:
            logger.info(f"Getting and saving accounts for user: {user_id}")
            
            # Get accounts from Plaid
            accounts_result = self.client.get_accounts(user_id, access_token)
            
            if not accounts_result["success"]:
                logger.error(f"Failed to get accounts for user {user_id}: {accounts_result.get('error')}")
                return accounts_result
            
            # Save accounts to database
            try:
                saved_count = save_plaid_accounts(user_id, accounts_result["accounts"])
                logger.info(f"Saved {saved_count} accounts to database for user: {user_id}")
                accounts_result["saved_count"] = saved_count
            except Exception as e:
                logger.error(f"Failed to save accounts to database for user {user_id}: {e}")
                accounts_result["save_error"] = str(e)
            
            return accounts_result
            
        except Exception as e:
            logger.error(f"Error in PlaidService.get_and_save_accounts for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def get_and_save_transactions(self, user_id: str, start_date: str = None, 
                                 end_date: str = None, count: int = 100, 
                                 access_token: str = None) -> Dict[str, Any]:
        """Get transaction data and save to database.
        
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
            logger.info(f"Getting and saving transactions for user: {user_id}")
            
            # Get transactions from Plaid
            transactions_result = self.client.get_transactions(user_id, start_date, end_date, count, access_token)
            
            if not transactions_result["success"]:
                logger.error(f"Failed to get transactions for user {user_id}: {transactions_result.get('error')}")
                return transactions_result
            
            # Save transactions to database
            try:
                saved_count = save_plaid_transactions(user_id, transactions_result["transactions"])
                logger.info(f"Saved {saved_count} transactions to database for user: {user_id}")
                transactions_result["saved_count"] = saved_count
            except Exception as e:
                logger.error(f"Failed to save transactions to database for user {user_id}: {e}")
                transactions_result["save_error"] = str(e)
            
            return transactions_result
            
        except Exception as e:
            logger.error(f"Error in PlaidService.get_and_save_transactions for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def sync_user_data(self, user_id: str, access_token: str = None) -> Dict[str, Any]:
        """Sync all Plaid data for a user (accounts and transactions).
        
        Args:
            user_id: User identifier
            access_token: Access token (if not provided, uses stored token)
            
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"Starting full data sync for user: {user_id}")
            
            # Sync accounts
            accounts_result = self.get_and_save_accounts(user_id, access_token)
            
            # Sync transactions
            transactions_result = self.get_and_save_transactions(user_id, access_token=access_token)
            
            # Combine results
            sync_result = {
                "success": accounts_result["success"] and transactions_result["success"],
                "user_id": user_id,
                "accounts": {
                    "success": accounts_result["success"],
                    "count": accounts_result.get("total_accounts", 0),
                    "saved_count": accounts_result.get("saved_count", 0),
                    "error": accounts_result.get("error")
                },
                "transactions": {
                    "success": transactions_result["success"],
                    "count": len(transactions_result.get("transactions", [])),
                    "saved_count": transactions_result.get("saved_count", 0),
                    "error": transactions_result.get("error")
                }
            }
            
            if sync_result["success"]:
                logger.info(f"Full data sync completed successfully for user: {user_id}")
            else:
                logger.warning(f"Full data sync completed with errors for user: {user_id}")
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error in PlaidService.sync_user_data for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def get_stored_data(self, user_id: str) -> Dict[str, Any]:
        """Get stored Plaid data for a user from database.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with stored data
        """
        try:
            logger.info(f"Getting stored data for user: {user_id}")
            return get_plaid_data(user_id)
            
        except Exception as e:
            logger.error(f"Error in PlaidService.get_stored_data for user {user_id}: {e}")
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
            return self.client.test_connection()
            
        except Exception as e:
            logger.error(f"Error in PlaidService.test_connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
