from fastapi import HTTPException, status


class StoreNotFound(HTTPException):
    def __init__(self, store_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )


class ReceiptNotFound(HTTPException):
    def __init__(self, receipt_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )