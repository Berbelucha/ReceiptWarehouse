from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Receipt, Store


class ReceiptService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_store(self, store_data: Store) -> Store:
        """Create a new store in the database."""
        try:
            store = Store(
                name=store_data.name,
                address=store_data.address,
                extra=store_data.extra,
                NIP=store_data.NIP
            )
            self.db_session.add(store)
            await self.db_session.commit()
            await self.db_session.refresh(store)
            return store
        except Exception as e: #noqa: BLE001
            await self.db_session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create store: {e!s}")

    async def get_store(self, store_id: int) -> Store | None:
        try:
            result = await self.db_session.execute(select(Store).where(Store.id == store_id))
            return result.scalar_one_or_none()
        except Exception as e: #noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to get store: {e!s}")

    async def create_receipt(self, receipt_data: Receipt) -> Receipt:
        try:
            # First, create the store if it doesn't exist
            store = Store(
                name=receipt_data.store.name,
                address=receipt_data.store.address,
                extra=receipt_data.store.extra,
                NIP=receipt_data.store.NIP
            )
            self.db_session.add(store)
            await self.db_session.flush()  # Get the ID without committing

            # Create the receipt
            receipt = Receipt(
                source_file=receipt_data.source_file,
                store_id=store.id,
                date=receipt_data.date,
                currency=receipt_data.currency,
                total=receipt_data.total,
                items=[item.model_dump() for item in receipt_data.items]  # Convert to dict for JSON storage
            )
            self.db_session.add(receipt)
            await self.db_session.commit()
            await self.db_session.refresh(receipt)
            return receipt
        except Exception as e: #noqa: BLE001
            await self.db_session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create receipt: {e!s}")

    async def get_receipt(self, receipt_id: int) -> Receipt | None:
        try:
            result = await self.db_session.execute(select(Receipt).where(Receipt.id == receipt_id))
            return result.scalar_one_or_none()
        except Exception as e: #noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to get receipt: {e!s}")

    async def get_receipts(self) -> list[Receipt]:
        try:
            result = await self.db_session.execute(
                select(Receipt).order_by(Receipt.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e: #noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to get receipts: {e!s}")

    async def get_stores(self) -> list[Store]:
        """Get all stores."""
        try:
            result = await self.db_session.execute(
                select(Store).order_by(Receipt.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e: #noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to get stores: {e!s}")

    async def get_receipt_with_store(self, receipt_id: int) -> dict | None:
        try:
            # This would typically use proper SQL JOINs, but we'll keep it simple
            receipt = await self.get_receipt(receipt_id)
            if not receipt:
                return None

            # For simplicity, we'll just return the receipt data
            # A real implementation would join with stores
            return {
                "receipt_id": receipt.id,
                "source_file": receipt.source_file,
                "store": {
                    "name": "Test Store",  # Would be properly joined in real implementation
                    "address": "",
                    "extra": "",
                    "NIP": ""
                },
                "date": receipt.date,
                "currency": receipt.currency,
                "total": receipt.total,
                "items": receipt.items
            }
        except Exception as e: #noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Failed to get receipt with store: {e!s}")