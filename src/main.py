"""
Main application entry point for ReceiptWarehouse.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from anyio import open_file
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status

from src.database import DatabaseService
from src.document_processing.router import router as documents_router
from src.mcp.router import router as mcp_router
from src.receipts.router import router as receipts_router
from src.settings import settings


@asynccontextmanager
async def lifespan(api: FastAPI):
    api.state.db = DatabaseService()
    await api.state.db.init_db()
    yield

# Create the FastAPI app
app = FastAPI(
    title="Receipt Warehouse API",
    description="API for managing receipts and related data",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include receipts router
app.include_router(documents_router)
app.include_router(receipts_router)
app.include_router(mcp_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return HTMLResponse(Path('src/index.html').read_text())

@app.post("/upload", )
async def upload(receipt_files: list[UploadFile]):
    results = []
    for file in receipt_files:
        content = await file.read()
        path = Path(settings.documents_dir.get('scan'), file.filename)
        async with await open_file(path, "wb") as f:
            await f.write(content)
        results.append({"filename": file.filename, "size": len(content)})
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    import hypercorn
    hypercorn.run(app, host="0.0.0.0", port=8000, http2=True, reload=True, bind="0.0.0.0:8000")
