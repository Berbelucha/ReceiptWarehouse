# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a receipt management application that processes scanned receipt documents, extracts structured data from them,
and stores the information in a SQLite database. The application uses Docling for OCR and document processing,
and includes functionality for document scanning, OCR correction, and metadata generation.

## Architecture

The application follows a layered architecture with the following components:

1. **API Layer**: FastAPI application with routers for receipts, documents, and MCP
2. **Service Layer**: Business logic for receipt operations and document processing
3. **Database Layer**: SQLModel-based database operations with SQLite
4. **Document Processing Layer**: Specialized services for scanning, OCR fixing, and metadata generation

### Key Components

- **Receipts Module**: Handles receipt CRUD operations with database integration
- **Document Processing Module**: Processes documents through multiple stages:
  - Scan service: Uses Docling for OCR and text extraction
  - OCR fix service: Applies LLM-based corrections to OCR output
  - Metadata service: Extracts structured data from processed documents
- **Database Service**: Manages SQLite connections and table creation

## Development Commands

### Setup and Installation

```bash
# Install dependencies
uv pip install -e .

# Run the application
uv run fastapi run src/main.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_file.py

# Run tests with coverage
uv run pytest --cov=src
```

### Development Server

```bash
# Start development server with hot reload
uv run fastapi run src/main.py --reload
```

### Database Operations

```bash
# Initialize database (automatically done on startup)
# No explicit command needed as it's handled in the FastAPI lifespan

# View database metadata
curl http://localhost:8000/metadata
```

## Code Structure

```
src/
├── main.py                 # FastAPI application entry point
├── database.py             # Database service with SQLite connection handling
├── receipt_service.py      # Service layer for receipt operations
├── models.py               # SQLModel database models (Store, Receipt, ReceiptItem)
├── schemas.py              # Pydantic models for data structures
├── settings.py             # Application settings
├── receipts/               # Receipt-related API endpoints
│   └── router.py           # Receipt API routes
├── document_processing/    # Document processing functionality
│   ├── router.py           # Document processing API routes
│   ├── service.py          # Main document processing service
│   ├── schemas.py          # Document processing schemas
│   └── services/           # Individual processing services
│       ├── scan_service.py     # Document scanning and OCR
│       ├── ocr_fix_service.py  # OCR correction with LLM
│       ├── metadata_service.py # Metadata generation
│       ├── receipt.py          # Receipt-specific parsing logic
│       └── receipt_preprocessor.py # Image preprocessing for receipts
└── test_database.py        # Database testing utilities
```

## Common Development Tasks

1. **Adding new receipt fields**: Modify `models.py` and `schemas.py` to add new fields to the Receipt model
2. **Adding new document processing steps**: Create new service classes in `src/document_processing/services/`
3. **Adding new API endpoints**: Add new routes in the appropriate router files (`receipts/router.py`, `document_processing/router.py`)
4. **Database schema changes**: Update models in `models.py` and run database initialization
5. **Tuning ReceiptPreprocessor parameters**: Use `ReceiptPreprocessorConfig` to adjust processing parameters without code changes

## Testing Strategy

The application uses pytest for testing. Tests should be placed in the `tests/` directory and follow the existing patterns. Key areas to test include:
- Database operations
- Receipt creation and retrieval
- Document processing workflows
- API endpoints