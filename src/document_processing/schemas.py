from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from src.settings import settings


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'

class DocumentProcessingRequest(BaseModel):
    directory: str = settings.documents_dir.get('scan')
    extensions: list[str] | None = None
    force: bool | None = False
    limit: int | None = 0

class OcrFixRequest(DocumentProcessingRequest):
    directory: str = settings.documents_dir.get('parsed')

class MetadataRequest(DocumentProcessingRequest):
    directory: str = settings.documents_dir.get('fixed')

class DocumentProcessingResult(BaseModel):
    file_path: str
    filename: str
    status: Status
    error_message: str | None = None
    processed_at: datetime = datetime.now()

class DocumentProcessingResponse(BaseModel):
    success: bool
    message: str
    results: list[DocumentProcessingResult]