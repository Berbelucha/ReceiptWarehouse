from datetime import datetime
from decimal import Decimal

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


class StoreCreate(SQLModel):
    name: str = "Unknown"
    address: str | None = None
    extra: str | None = None
    NIP: str | None = None

class StorePublic(StoreCreate):
    id: int

class ReceiptItemCreate(SQLModel):
    name: str = "[Produkt]"
    quantity: Decimal = Decimal(1)
    price: Decimal | None = None
    total: Decimal | None = None
    tags: str | None = None

class ReceiptItemPublic(ReceiptItemCreate):
    id: int

class ReceiptCreate(SQLModel):
    source_file: str
    store: StoreCreate | None = None
    date: NaiveDatetime | None = None
    currency: str = "PLN"
    total: Decimal | None = None
    items: list[ReceiptItemCreate] = Field(default_factory=list)

class ReceiptPublic(ReceiptCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None
