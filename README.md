# ReceiptWarehouse

Self-improvement project designed to learn Python (FastAPI) and principles and techniques for data preparation and 
parsing for RAG.

### Requirements:
- fully local
- FOSS LLM model only
- privacy and security
- low hardware requirements: has to run on up to 16GB VRAM (RTX 4070 Ti Super), preferably no more than 8GB

### Status:
- initial setup
- receipt scan/photos image preprocessing for stabilizing OCR results
- OCR of receipt scan/photos with custom output builder
  - custom builder was created to overcome random output generation from Docling
  - Docling has access to well-defined OCR result set, just their output templating doesn't behave in deterministic way
- Initial implementation of local Gemma4 model for result postprocessing
  - fixing typos and simple OCR errors
  - generating better structured Markdown file (human-readable) based on predefined template
- Initial metadata generation based on structured Markdown files
- Initial SQLite setup for data storage

### TO DO:
- tune Gemma4 OCR fixing
- replace the order of operation for metadata/Markdown generation
  - generate JSON metadata first to have computer-readable, structured input
  - generate Markdown template with deterministic algorith rather than rely on LLM
- generate embeddings to feed into Vector Database (Qdrant?)
  - VERIFY: how much would I get from relation built into vector-powered RAG?
  - still implement to learn the process
- create React based UI to allow easier access to application
  - introduce Mobile app