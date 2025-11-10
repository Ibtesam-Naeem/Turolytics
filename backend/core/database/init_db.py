# ------------------------------ IMPORTS ------------------------------
"""
Database initialization script.

Run this script to create all database tables.
Usage: python -m core.database.init_db
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import init_db, engine
from core.config.settings import settings

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ------------------------------ MAIN ------------------------------

def main():
    """Initialize database tables."""
    try:
        logger.info(f"Connecting to database: {settings.database.database}")
        logger.info(f"Database URL: {settings.database.database_url.split('@')[1] if '@' in settings.database.database_url else 'hidden'}")
        
        init_db()
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

