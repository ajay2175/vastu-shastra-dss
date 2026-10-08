"""
Configuration settings for Vastu Shastra DSS.

Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Vastu Shastra Decision Support System"
    api_version: str = "1.0.0"
    debug: bool = False

    # Anthropic API
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-opus-4-1-20250805"
    anthropic_timeout: int = 60

    # Primary Vector Database (Qdrant)
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    # Specialized Vector Databases
    jyotish_vdb_url: Optional[str] = None
    jyotish_vdb_key: Optional[str] = None
    ayurveda_vdb_url: Optional[str] = None
    ayurveda_vdb_key: Optional[str] = None

    # Local Chroma Database
    chroma_db_path: str = "./data/embeddings"
    chroma_collection_name: str = "vastu_shastra"
    embedding_model: str = "paraphrase-multilingual-mpnet-base-v2"

    # Logging
    log_level: str = "INFO"

    # Feature Flags
    enable_rag: bool = True
    enable_kg_reasoning: bool = True
    enable_hybrid_search: bool = True
    enable_degradation: bool = True

    # Performance Tuning
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 30
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Optional[Path] = None
    kg_dir: Optional[Path] = None
    vastu_texts_dir: Optional[Path] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Set derived paths
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.kg_dir is None:
            self.kg_dir = self.data_dir / "kg"
        if self.vastu_texts_dir is None:
            self.vastu_texts_dir = self.data_dir / "vastu_texts"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

    def validate_required_settings(self) -> list[str]:
        """Validate that required settings are present."""
        errors = []
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        return errors


# Global settings instance
settings = Settings()
