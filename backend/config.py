"""
Configuration Module
Manages all environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic for validation and type safety.
    """
    
    # Google Gemini API Key (REQUIRED)
    google_api_key: str
    
    # Chunking Strategy
    # CHUNK_SIZE: Number of characters per chunk
    # Smaller = more precise retrieval, but may lose context
    # Larger = better context, but less precise matching
    chunk_size: int = 1000
    
    # CHUNK_OVERLAP: Characters shared between consecutive chunks
    # Prevents information loss at chunk boundaries
    chunk_overlap: int = 200
    
    # Retrieval Configuration
    # TOP_K_RETRIEVAL: Number of most similar chunks to retrieve
    # Balance between context size and relevance
    top_k_retrieval: int = 4
    
    # LLM Temperature (0.0 = deterministic, 1.0 = creative)
    # Keep low for legal analysis to reduce hallucination
    temperature: float = 0.1
    
    # Storage Paths
    pdf_storage_path: str = "./data/pdfs"
    faiss_index_path: str = "./data/faiss_index"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Creates and caches a single Settings instance.
    lru_cache ensures we don't re-read .env on every call.
    """
    return Settings()


# Ensure required directories exist
def ensure_directories():
    """
    Create necessary directories if they don't exist.
    Called on application startup.
    """
    settings = get_settings()
    os.makedirs(settings.pdf_storage_path, exist_ok=True)
    os.makedirs(settings.faiss_index_path, exist_ok=True)
