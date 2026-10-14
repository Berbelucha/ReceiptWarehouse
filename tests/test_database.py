"""
Test script to verify database service functionality.
"""
import asyncio

from src.database import DatabaseService


async def test_database_service():
    """Test the database service functionality."""
    # Initialize the database service
    db_service = DatabaseService("sqlite:///test_receipt_warehouse.db")

    # Initialize database
    await db_service.init_db()
    print("Database initialized successfully")


    print("Database service tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_database_service())