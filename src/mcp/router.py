"""
Receipts module for handling receipt-related API endpoints.
"""
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime

from src.helpers import DateRange, Period, get_receipt_service, period_bounds
from src.receipt_service import ReceiptService

# Create API router for receipts
router = APIRouter(
    prefix="/mcp",
    tags=["mcp"]
)


def _to_naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(UTC).replace(tzinfo=None)


def get_date_range(
    period: Period = Query(Period.month),
    date_from: AwareDatetime | None = Query(None, alias="from"),
    date_to: AwareDatetime | None = Query(None, alias="to"),
) -> DateRange:
    anchor = date_from or date_to or datetime.now(UTC)
    defaults = period_bounds(period, anchor)

    start = date_from or defaults.start
    end = date_to or defaults.end
    if start >= end:
        raise HTTPException(422, "`from` must be earlier than `to`")
    return DateRange(_to_naive_utc(start), _to_naive_utc(end))


@router.get("/", response_model=Decimal)
async def get_expenses_total(
        receipt_service: ReceiptService = Depends(get_receipt_service),
        store_name: str | None = Query(None),
        date_range: DateRange = Depends(get_date_range),
):
    """
    Get a list of receipts with optional filtering.

    Query Parameters:
    - store_name: Filter by store name
    - date_from: Filter by date (inclusive)
    - date_to: Filter by date (inclusive)
    - period: "month" or "year"
    """
    try:
        # For simplicity, we'll get all receipts and apply filters in-memory
        # In a real implementation, we'd build a proper SQL query
        receipts = await receipt_service.get_receipts()
        filtered_receipts = []

        for receipt in receipts:
            # Apply filters
            if store_name is not None and receipt.store.name.lower().find(store_name.lower()) == -1:
                continue
            if date_range is not None and receipt.date and receipt.date < date_range.start:
                continue
            if date_range is not None and receipt.date and receipt.date > date_range.end:
                continue

            filtered_receipts.append(receipt)

        # Convert to response format
        result = 0
        for receipt in filtered_receipts:
            result += receipt.total

        return result

    except Exception as e: #noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error retrieving receipts: {e!s}")
