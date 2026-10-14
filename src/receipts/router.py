import logging
import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from src.helpers import get_receipt_service
from src.models import Receipt
from src.receipt_service import ReceiptService
from src.schemas import ReceiptCreate, ReceiptPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/receipts",
    tags=["receipts"]
)


@router.get("/", response_model=list[ReceiptPublic])
async def list_receipts(
    receipt_service: ReceiptService = Depends(get_receipt_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000, ge=1),
    store_id: int | None = Query(None),
    store_name: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None)
):
    """
    Get a list of receipts with optional filtering.

    Query Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default: 100, max: 1000)
    - store_id: Filter by store ID
    - store_name: Filter by store name
    - date_from: Filter by date (inclusive)
    - date_to: Filter by date (inclusive)
    """
    try:
        # In a real implementation, we'd build a proper SQL query
        receipts = await receipt_service.get_receipts()
        filtered_receipts = []

        for receipt in receipts:
            # Apply filters
            if store_id is not None and receipt.store_id != store_id:
                continue
            if store_name is not None and receipt.store.name.lower().find(store_name.lower()) == -1:
                continue
            if date_from is not None and receipt.date and receipt.date < date_from:
                continue
            if date_to is not None and receipt.date and receipt.date > date_to:
                continue

            filtered_receipts.append(receipt)

        # Apply pagination
        paginated = filtered_receipts[skip:skip + limit]

        # Convert to response format
        result = []
        for receipt in paginated:
            result.append({
                "id": receipt.id,
                "source_file": receipt.source_file,
                "store_id": receipt.store_id,
                "date": receipt.date,
                "currency": receipt.currency,
                "total": receipt.total,
                "items": receipt.items
            })

        return paginated

    except Exception as e: #noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error retrieving receipts: {e!s}")

@router.get("/{receipt_id}", response_model=Receipt)
async def get_receipt(
    receipt_id: int,
    receipt_service: ReceiptService = Depends(get_receipt_service)
):
    """
    Get a specific receipt by ID.

    Args:
        :param receipt_id: The ID of the receipt to retrieve
        :param receipt_service:
    """
    try:
        receipt = await receipt_service.get_receipt(receipt_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        return {
            "id": receipt.id,
            "source_file": receipt.source_file,
            "store_id": receipt.store_id,
            "date": receipt.date,
            "currency": receipt.currency,
            "total": receipt.total,
            "items": receipt.items
        }

    except Exception as e: #noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error retrieving receipt: {e!s}")

@router.get("/stores/{store_id}", response_model=list[Receipt])
async def get_receipts_by_store(
    store_id: int,
    receipt_service: ReceiptService = Depends(get_receipt_service)
):
    """
    Get all receipts for a specific store.

    Args:
        :param store_id: The ID of the store
        :param receipt_service:
    """
    try:
        # In a real implementation, this would query the database properly
        # For now, we'll use the existing get_receipts and filter in-memory
        receipts = await receipt_service.get_receipts()
        store_receipts = []

        for receipt in receipts:
            if receipt.store_id == store_id:
                store_receipts.append({
                    "id": receipt.id,
                    "source_file": receipt.source_file,
                    "date": receipt.date,
                    "currency": receipt.currency,
                    "total": receipt.total,
                    "items": receipt.items
                })

        return store_receipts

    except Exception as e: #noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error retrieving store receipts: {e!s}")


@router.post("/", response_model=ReceiptPublic)
async def create_receipt(
    receipt_data: ReceiptCreate,
    receipt_service: ReceiptService = Depends(get_receipt_service)
):
    """
    Create a new receipt in the database.

    Args:
        receipt_data: The receipt data to create
        :param receipt_data:
        :param receipt_service:
    """
    try:
        receipt = await receipt_service.create_receipt(receipt_data)
        return receipt
    except Exception as e: #noqa: BLE001
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error creating receipt: {e!s}")