import logging
import traceback
from datetime import datetime
from pathlib import Path

from anyio import open_file
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    LayoutObjectDetectionOptions,
    OcrMode,
    PdfPipelineOptions,
    RapidOcrOptions,
)
from docling.datamodel.settings import settings as doc_settings
from docling.document_converter import DocumentConverter, ImageFormatOption

from src.document_processing.schemas import DocumentProcessingResult, Status
from src.document_processing.services.line_rebuilder import rebuild_lines_from_cells
from src.document_processing.services.receipt_preprocessor import ReceiptPreprocessor
from src.settings import settings

logger = logging.getLogger(__name__)
doc_settings.debug.visualize_ocr = True
doc_settings.debug.debug_output_path = "./debug"


def _setup_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions(
        generate_parsed_pages=True,
        do_ocr=True,
        do_table_structure=False,
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CUDA,
        ),
        layout_options=LayoutObjectDetectionOptions.from_preset("layout_egret_xlarge"),
        ocr_options=RapidOcrOptions(
            backend="onnxruntime",
            lang=["pl"],
            mode=OcrMode.FULL_PAGE,
            use_cls=False,
            scale=1.5,
            text_score=0.6,
            model_size="medium",
            rapidocr_params={
                "EngineConfig.onnxruntime.use_cuda": True,
                "EngineConfig.onnxruntime.cuda_ep_cfg.device_id": 1,
            },
        ),
    )

    return DocumentConverter(
        format_options={
            InputFormat.IMAGE: ImageFormatOption(
                pipeline_options=pipeline_options,
            ),
        }
    )


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


class DocumentScanService:
    def __init__(self):
        self.converter = _setup_converter()

    async def scan_directory(
        self,
        directory: str,
        extensions: list[str],
        force: bool = False,
        limit: int = 0,
    ) -> list[DocumentProcessingResult]:
        results = []
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        file_paths = []
        for item in directory_path.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                if ext in [f".{ext}" for ext in extensions]:
                    file_paths.append(item)

        for i, file_path in enumerate(sorted(file_paths)):
            try:
                result = await self._process_document(file_path, force)
                results.append(result)
                logger.debug("Processed: %s", file_path.name)
                print_percent_done(i, limit if limit > 0 else len(file_paths))
                if limit > 0 and i >= limit - 1:
                    break
            except Exception as e:
                logger.exception(f"Error processing {file_path}")
                results.append(
                    DocumentProcessingResult(
                        file_path=str(file_path),
                        filename=file_path.name,
                        status=Status.ERROR,
                        error_message=str(e),
                        processed_at=datetime.now(),
                    )
                )

        return results

    async def _process_document(
        self, file_path: Path, force: bool = False
    ) -> DocumentProcessingResult:
        try:
            parsed_path = Path(settings.documents_dir.get("parsed"))
            if not parsed_path.exists():
                parsed_path.mkdir(parents=True, exist_ok=True)

            new_file_path = parsed_path / f"{file_path.name}".replace(".jpg", ".json")
            new_file_path2 = parsed_path / f"{file_path.name}".replace(".jpg", ".md")

            if new_file_path.exists() and not force:
                logger.info(f"File {file_path} already parsed, skipping")
                return DocumentProcessingResult(
                    file_path=str(file_path),
                    filename=file_path.name,
                    status=Status.SUCCESS,
                    processed_at=datetime.now(),
                )

            preprocessor = ReceiptPreprocessor(
                perspective=True, textline_dewarp=True, deskew=True
            )

            stream = preprocessor.process(file_path.read_bytes(), file_path.name)
            doc = self.converter.convert(stream)
            doc.document = rebuild_lines_from_cells(doc.document, page=doc.pages[0])
            doc.document.save_as_json(new_file_path)

            async with await open_file(new_file_path2, "w") as f:
                markdown_content = doc.document.export_to_markdown()
                await f.write(markdown_content)

            return DocumentProcessingResult(
                file_path=str(file_path),
                filename=file_path.name,
                status=Status.SUCCESS,
                processed_at=datetime.now(),
            )

        except Exception as e:
            logger.exception(f"Error processing document {file_path}")
            logger.error(traceback.format_exc())
            return DocumentProcessingResult(
                file_path=str(file_path),
                filename=file_path.name,
                status=Status.ERROR,
                error_message=str(e),
                processed_at=datetime.now(),
            )
