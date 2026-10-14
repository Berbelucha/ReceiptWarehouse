import logging

from fastapi import APIRouter, HTTPException, status

from src.document_processing.schemas import (
    DocumentProcessingRequest,
    DocumentProcessingResponse,
    MetadataRequest,
    OcrFixRequest,
)
from src.document_processing.service import DocumentProcessingService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

document_service = DocumentProcessingService()

@router.post("/scan", response_model=DocumentProcessingResponse)
async def scan_documents(request: DocumentProcessingRequest):
    """
    Scan and process all documents in the specified directory.

    This will process all files with the given extensions and upload them
    to the document processing system.
    """
    try:
        logger.info(f"Scanning directory: {request.directory}")
        results = await document_service.scan_directory(
            directory=request.directory,
            extensions=request.extensions or ['pdf', 'jpg', 'jpeg', 'png'],
            force=request.force,
            limit=request.limit,
        )

        return DocumentProcessingResponse(
            success=True,
            message=f"Successfully processed {len(results)} documents",
            results=results
        )
    except Exception as e: #noqa: BLE001
        logger.error(f"Error processing documents: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing documents: {e!s}"
        )

@router.post("/fix-ocr", response_model=DocumentProcessingResponse)
async def fix_ocr(request: OcrFixRequest):
    """
    Fix OCR issues for documents in the specified directory.
    """
    try:
        logger.info(f"Fixing OCR for directory: {request.directory}")
        results = await document_service.fix_ocr_directory(
            directory=request.directory
        )

        return DocumentProcessingResponse(
            success=True,
            message=f"Successfully fixed OCR for {len(results)} documents",
            results=results
        )
    except Exception as e: #noqa: BLE001
        logger.error(f"Error fixing OCR: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fixing OCR: {e!s}"
        )

@router.post("/generate-metadata", response_model=DocumentProcessingResponse)
async def generate_metadata(request: MetadataRequest):
    """
    Generate metadata for documents in the specified directory.
    """
    try:
        logger.info(f"Generating metadata for directory: {request.directory}")
        results = await document_service.generate_metadata_directory(
            directory=request.directory
        )

        return DocumentProcessingResponse(
            success=True,
            message=f"Successfully generated metadata for {len(results)} documents",
            results=results
        )
    except Exception as e: #noqa: BLE001
        logger.error(f"Error generating metadata: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating metadata: {e!s}"
        )
