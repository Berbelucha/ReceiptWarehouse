import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, database_url: str = "sqlite+aiosqlite:///receipt_warehouse.db"):
        self.database_url = database_url
        self.engine: AsyncEngine
        self.async_sessionmaker: async_sessionmaker[AsyncSession]

    async def init_db(self):
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=True,
                pool_pre_ping=True,
                poolclass=NullPool
            )

            def create_tables(connection: Connection) -> None:
                SQLModel.metadata.create_all(connection)

            async with self.engine.begin() as conn:
                await conn.run_sync(create_tables)

            self.async_sessionmaker = async_sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

            logger.debug("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.async_sessionmaker:
            await self.init_db()

        async with self.async_sessionmaker() as session:
            yield session
