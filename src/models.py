from datetime import UTC, datetime
from decimal import Decimal

from pydantic import NaiveDatetime
from sqlalchemy import DateTime, func
from sqlmodel import Field, Relationship, SQLModel


class Store(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True, nullable=False, unique=True)
    address: str | None = Field(default=None)
    extra: str | None = Field(default=None)
    NIP: str | None = Field(index=True, default=None, unique=True)
    receipts: list["Receipt"] = Relationship(back_populates="store")
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            'onupdate': func.now(),
            'server_default': func.now(),
        },
    )

class ReceiptItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    receipt_id: int = Field(foreign_key="receipt.id", nullable=False)
    name: str = Field(index=True, nullable=False, default="[Produkt]")
    quantity: Decimal = Field(default=1, decimal_places=3)
    price: Decimal | None = Field(default=None, decimal_places=2)
    total: Decimal | None = Field(default=None, decimal_places=2)
    tags: str = Field(default="", nullable=False)
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            'onupdate': func.now(),
            'server_default': func.now(),
        },
    )

class Receipt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    source_file: str = Field(nullable=False, unique=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    store: Store = Relationship(back_populates="receipts")
    date: NaiveDatetime | None = Field(default=None)
    currency: str = Field(default="PLN")
    total: Decimal | None = Field(default=None, decimal_places=2)
    items: list["ReceiptItem"] = Relationship()
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            'onupdate': func.now(),
            'server_default': func.now(),
        },
    )

