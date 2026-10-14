from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from fastapi import Request

from src.receipt_service import ReceiptService


def get_receipt_service(request: Request) -> ReceiptService:
    return request.app.state.db

class Period(str, Enum):
    month = "month"
    year = "year"


@dataclass(frozen=True)
class DateRange:
    start: datetime  # inclusive
    end: datetime    # exclusive


def period_bounds(period: Period, anchor: datetime) -> DateRange:
    if period is Period.month:
        start = anchor.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
    else:
        start = anchor.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
    return DateRange(start, end)