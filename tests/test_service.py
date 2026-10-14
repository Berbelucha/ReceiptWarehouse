"""
Test script to verify database service works correctly.
"""
import asyncio
import logging
import sys

from src.database import DatabaseService

logger = logging.getLogger(__name__)

async def test_database():
    """Test the database service functionality."""
    print("Testing database service...")

    # Initialize the database service
    db_service = DatabaseService("sqlite:///test_receipt_warehouse.db")

    try:
        # Initialize database
        await db_service.init_db()
        print("✓ Database initialized successfully")

        print("All tests passed!")
        return True

    except Exception:
        logger.exception("x Error:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)