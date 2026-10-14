import logging
import traceback
from datetime import datetime
from pathlib import Path

from anyio import open_file

from src.document_processing.schemas import DocumentProcessingResult, Status
from src.document_processing.services.receipt import generate_metadata_json
from src.settings import settings

logger = logging.getLogger(__name__)

LLAMA_API_URL = "http://localhost:8080"
LLAMA_API_URL_CHAT = f"{LLAMA_API_URL}/chat/completions"
LLAMA_API_URL_MODELS = f"{LLAMA_API_URL}/models"

class DocumentMetadataService:
    def __init__(self):
        pass

    async def generate_metadata_directory(self, directory: str) -> list[DocumentProcessingResult]:
        results = []
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        file_paths = []
        for item in directory_path.iterdir():
            if item.is_file() and item.suffix.lower() == '.md':
                file_paths.append(item)

        for file_path in sorted(file_paths):
            try:
                result = await self._generate_metadata_file(file_path)
                results.append(result)
            except Exception as e:
                logger.exception(f"Error generating metadata for {file_path}")
                results.append(DocumentProcessingResult(
                    file_path=str(file_path),
                    filename=file_path.name,
                    status=Status.ERROR,
                    error_message=str(e),
                    processed_at=datetime.now()
                ))

        return results

    async def _generate_metadata_file(self, file_path: Path) -> DocumentProcessingResult:
        try:
            metadata = generate_metadata_json(file_path)
            metadata_path = Path(settings.documents_dir.get('metadata'))
            if not metadata_path.exists():
                metadata_path.mkdir(parents=True, exist_ok=True)
            new_file_path = metadata_path / f"{file_path.name}".replace(".md", ".json")

            async with await open_file(new_file_path, "w") as f:
                await f.write(metadata.model_dump_json(indent=2))

            return DocumentProcessingResult(
                file_path=str(file_path),
                filename=file_path.name,
                status=Status.SUCCESS,
                processed_at=datetime.now()
            )

        except Exception as e:
            logger.exception(f"Error generating metadata for {file_path}")
            logger.error(traceback.format_exc())
            return DocumentProcessingResult(
                file_path=str(file_path),
                filename=file_path.name,
                status=Status.ERROR,
                error_message=str(e),
                processed_at=datetime.now()
            )