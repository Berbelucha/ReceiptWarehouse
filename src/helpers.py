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

# Source - https://stackoverflow.com/a/61433559
# Posted by Ivan Procopovich, modified by community. See post 'Timeline' for change history
# Retrieved 2026-11-09, License - CC BY-SA 4.0
def print_percent_done(index, total, bar_len=50, title="Please wait"):
    """
    index is expected to be 0 based index.
    0 <= index < total
    """
    percent_done = (index + 1) / total * 100
    percent_done = round(percent_done, 1)

    done = round(percent_done / (100 / bar_len))
    togo = bar_len - done

    done_str = "█" * int(done)
    togo_str = "░" * int(togo)

    print(
        f"\t⏳{title}: [{done_str}{togo_str}] {percent_done}% done [{index + 1}/{total}]",
        end="\r",
    )

    if round(percent_done) == 100:
        print("\t✅")