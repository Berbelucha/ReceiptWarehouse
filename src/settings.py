from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    documents_dir: dict[str, str] = {
        "scan": "documents/scans",
        "parsed": "documents/parsed",
        "fixed": "documents/fixed",
        "metadata": "documents/metadata",
    }

settings = Settings()