import logging

from src.document_processing.schemas import DocumentProcessingResult
from src.document_processing.services.metadata_service import DocumentMetadataService
from src.document_processing.services.ocr_fix_service import DocumentOcrFixService
from src.document_processing.services.scan_service import DocumentScanService

logger = logging.getLogger(__name__)

LLAMA_API_URL = "http://localhost:8080"
LLAMA_API_URL_CHAT = f"{LLAMA_API_URL}/chat/completions"
LLAMA_API_URL_MODELS = f"{LLAMA_API_URL}/models"

class DocumentProcessingService:
    def __init__(self):
        self.file_extensions = {
            "image": [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"],
            "pdf": [".pdf"]
        }
        self.converter = None
        self.scan_service = DocumentScanService()
        self.ocr_fix_service = DocumentOcrFixService()
        self.metadata_service = DocumentMetadataService()

    async def scan_directory(self, directory: str, extensions: list[str], force = False, limit = 0) -> list[DocumentProcessingResult]:
        return await self.scan_service.scan_directory(directory, extensions, force, limit)

    async def scan_file(self, filename: str, directory: str, force = False) -> list[DocumentProcessingResult]:
        return await self.scan_service.scan_file(filename, directory, force)

    async def fix_ocr_directory(self, directory: str) -> list[DocumentProcessingResult]:
        return await self.ocr_fix_service.fix_ocr_directory(directory)

    async def generate_metadata_directory(self, directory: str) -> list[DocumentProcessingResult]:
        return await self.metadata_service.generate_metadata_directory(directory)