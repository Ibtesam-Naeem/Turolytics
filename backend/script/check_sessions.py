#!/usr/bin/env python3
"""
Script to check if user sessions are being stored in the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from core.database.connection import engine, SessionLocal
from core.database.models import UserSession, Account
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_sessions():
    """Check if sessions table exists and has data."""
    db = SessionLocal()
    try:
        # Check if table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("=" * 60)
        logger.info("Checking user_sessions table...")
        logger.info("=" * 60)
        
        if 'user_sessions' not in tables:
            logger.error("✗ user_sessions table does NOT exist!")
            logger.info("  Run: python backend/script/create_user_sessions_table.py")
            logger.info("  Or restart the backend server to create it automatically")
            return
        
        logger.info("✓ user_sessions table exists")
        
        # Check table structure
        columns = inspector.get_columns('user_sessions')
        logger.info(f"\nTable columns: {[col['name'] for col in columns]}")
        
        # Count sessions
        session_count = db.query(UserSession).count()
        logger.info(f"\nTotal sessions in database: {session_count}")
        
        if session_count > 0:
            # Show some sessions
            sessions = db.query(UserSession).limit(5).all()
            logger.info("\nSample sessions:")
            for session in sessions:
                account = db.query(Account).filter(Account.id == session.account_id).first()
                logger.info(f"  - Session ID: {session.id}")
                logger.info(f"    Account: {account.email if account else 'Unknown'} (ID: {session.account_id})")
                logger.info(f"    Device: {session.browser} on {session.os}")
                logger.info(f"    IP: {session.ip_address}")
                logger.info(f"    Created: {session.created_at}")
                logger.info(f"    Last Used: {session.last_used_at}")
                logger.info(f"    Active: {session.is_active}")
                logger.info("")
        else:
            logger.warning("⚠ No sessions found in database!")
            logger.info("  This could mean:")
            logger.info("  1. No one has logged in since sessions were implemented")
            logger.info("  2. Session creation is failing (check backend logs)")
            logger.info("  3. Sessions are being created but query is failing")
        
        # Check for active sessions
        active_count = db.query(UserSession).filter(UserSession.is_active == 1).count()
        logger.info(f"Active sessions: {active_count}")
        
    except Exception as e:
        logger.error(f"Error checking sessions: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    check_sessions()


