from sqlalchemy.orm import selectinload
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import DatabaseService
from src.models import Receipt, ReceiptItem, Store
from src.schemas import ReceiptCreate, StoreCreate


class ReceiptService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def create_store(self, store_data: StoreCreate) -> Store:
        async with self.db_service.get_session() as session:
            store = Store(
                **store_data.model_dump()
            )
            session.add(store)
            await session.commit()
            await session.refresh(store)
            return store

    async def get_store(self, store_id: int) -> Store | None:
        async with self.db_service.get_session() as session:
            return await session.get(Store, store_id)

    @staticmethod
    async def _create_store(store_data: StoreCreate | None, session: AsyncSession) -> Store:
        store_data = store_data or StoreCreate()
        query = select(Store).where(or_(Store.name == store_data.name, Store.NIP == store_data.NIP))
        store = (await session.exec(query)).first()

        if store is None:
            store = Store(
                **store_data.model_dump()
            )

        session.add(store)
        await session.flush()  # Get the ID without committing

        return store

    async def create_receipt(self, receipt_data: ReceiptCreate) -> Receipt:
        async with (self.db_service.get_session() as session):
            store = await self._create_store(receipt_data.store, session)

            receipt = Receipt(
                source_file=receipt_data.source_file,
                store_id=store.id,
                date=receipt_data.date,
                currency=receipt_data.currency,
                total=receipt_data.total
            )
            session.add(receipt)
            await session.flush()

            for item in receipt_data.items:
                receipt_item = ReceiptItem(
                    receipt_id=receipt.id,
                    **item.model_dump(),
                )
                session.add(receipt_item)

            await session.commit()

            query = select(Receipt).where(Receipt.id == receipt.id).options(
                        selectinload(Receipt.store),
                        selectinload(Receipt.items),
                    )
            receipt = await session.exec(query)

            return receipt.first()

    async def get_receipt(self, receipt_id: int) -> Receipt | None:
        async with self.db_service.get_session() as session:
            query = select(Receipt).where(Receipt.id == receipt_id).options(
                selectinload(Receipt.store),
                selectinload(Receipt.items),
            )
            receipt = await session.exec(query)
            return receipt.first()

    async def get_receipts(self) -> list[Receipt]:
        async with self.db_service.get_session() as session:
            query = select(Receipt).options(
                selectinload(Receipt.store),
                selectinload(Receipt.items),
            )
            result = await session.exec(query)
            return result.all()

    async def get_stores(self) -> list[Store]:
        async with self.db_service.get_session() as session:
            result = await session.exec(select(Store))
            return result.all()