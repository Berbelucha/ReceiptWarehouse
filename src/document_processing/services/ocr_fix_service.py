import json
import logging
import time
import traceback
from datetime import datetime
from pathlib import Path

import requests
from anyio import open_file

from src.document_processing.schemas import DocumentProcessingResult, Status
from src.settings import settings

logger = logging.getLogger(__name__)

LLAMA_API_URL = "http://localhost:8080"
LLAMA_API_URL_CHAT = f"{LLAMA_API_URL}/chat/completions"
LLAMA_API_URL_MODELS = f"{LLAMA_API_URL}/models"


class DocumentOcrFixService:
    def __init__(self):
        pass

    async def fix_ocr_directory(self, directory: str) -> list[DocumentProcessingResult]:
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
                result = await self._fix_ocr_file(file_path)
                results.append(result)
            except Exception as e:
                logger.exception(f"Error fixing OCR for {file_path}")
                results.append(DocumentProcessingResult(
                    file_path=str(file_path),
                    filename=file_path.name,
                    status=Status.ERROR,
                    error_message=str(e),
                    processed_at=datetime.now()
                ))

        return results

    async def _fix_ocr_file(self, file_path: Path) -> DocumentProcessingResult:
        try:
            fixed_path = Path(settings.documents_dir.get('fixed'))
            if not fixed_path.exists():
                fixed_path.mkdir(parents=True, exist_ok=True)

            new_file_path = fixed_path / f"{file_path.name}"

            if new_file_path.exists():
                logger.info(f"File {new_file_path} already fixed, skipping")
                return DocumentProcessingResult(
                    file_path=str(new_file_path),
                    filename=new_file_path.name,
                    status=Status.SUCCESS,
                    processed_at=datetime.now()
                )

            markdown_content = file_path.read_text(encoding='utf-8', errors='ignore')
            completion = self._process_ocr_text(markdown_content)
            if not completion:
                DocumentProcessingResult(
                    file_path=str(new_file_path),
                    filename=new_file_path.name,
                    status=Status.ERROR,
                    error_message="Failed to fix OCR",
                    processed_at=datetime.now()
                )
            else:
                async with await open_file(new_file_path, 'w') as f:
                    await f.write(completion)

            return DocumentProcessingResult(
                file_path=str(new_file_path),
                filename=new_file_path.name,
                status=Status.SUCCESS,
                processed_at=datetime.now()
            )

        except Exception as e:
            logger.exception(f"Error fixing OCR for {file_path}")
            logger.error(traceback.format_exc())
            return DocumentProcessingResult(
                file_path=str(file_path),
                filename=file_path.name,
                status=Status.ERROR,
                error_message=str(e),
                processed_at=datetime.now()
            )

    def _wait_for_model(self, model_name: str, timeout: int = 60) -> None:
        url = f"{LLAMA_API_URL_MODELS}"
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            models = response.json().get("data", [])
            model = next(
                (m for m in models if m.get("id") == model_name),
                None,
            )

            if model and model.get("status").get('value') == "loaded":
                return

            time.sleep(2)

        raise TimeoutError(
            f"Model {model_name} nie załadował się w ciągu {timeout} sekund."
        )

    def _process_ocr_text(self, ocr_text: str) -> str:
        start_time = time.time()

        prompt = Path('src/document_processing/GEMMA_PROMPT_EN.md').read_text()

        response = requests.post(
            LLAMA_API_URL_CHAT,
            json={
                "model": "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_M",
                "messages": [
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": f"Parse this OCR output according to system rules:\n\n{ocr_text}",
                    },
                ],
                # "tools": [
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "duckduckgo_search",
                #             "description": "Search the web using DuckDuckGo.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "query": {"type": "string"},
                #                     "max_results": {"type": "integer"},
                #                     "region": {"type": "string"}
                #                 },
                #                 "required": ["query"]
                #             }
                #         }
                #     }
                # ],
                # "tool_choice": "required",
                "stream": True
            },
            stream=True,
        )

        collected_chunks = []
        collected_messages = []

        # iterate through the stream of events
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')

                if decoded_line.startswith('data:'):
                    json_data = decoded_line[len('data:'):].strip()

                    if json_data == '[DONE]':
                        logger.debug("Stream completed")
                        break

                    try:
                        chunk = json.loads(json_data)
                        chunk_time = time.time() - start_time
                        collected_chunks.append(chunk)

                        if chunk.get('choices'):
                            chunk_message = chunk['choices'][0]['delta'].get('content', '')  # get message
                            if chunk_message:
                                collected_messages.append(chunk_message)  # save message
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON: {e}")
                        continue

        if 'chunk_time' not in locals():
            logger.error("No valid response received from the server")

        collected_messages = [m for m in collected_messages if m]
        full_reply_content = ''.join(collected_messages)
        logger.debug(f"Full conversation received: {full_reply_content}")

        response.raise_for_status()
        return full_reply_content
