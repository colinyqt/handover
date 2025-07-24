# overhaul/core/config.py
"""
Centralized configuration for all paths and environment variables.
Edit this file to change model/database/output locations for local/server use.
"""
import os
from pathlib import Path

# Base directory (relative to this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Embedding model path
EMBEDDING_MODEL_PATH = os.environ.get(
    "EMBEDDING_MODEL_PATH",
    str(BASE_DIR / "jina_reranker" / "minilm-embedding")
)

# Reranker model path
RERANKER_MODEL_PATH = os.environ.get(
    "RERANKER_MODEL_PATH",
    str(BASE_DIR / "jina_reranker" / "cross-encoder")
)

# Database paths
METERS_DB_PATH = os.environ.get(
    "METERS_DB_PATH",
    str(BASE_DIR / "overhaul" / "databases" / "meters.db")
)
TEST_METERS_DB_PATH = os.environ.get(
    "TEST_METERS_DB_PATH",
    str(BASE_DIR / "overhaul" / "databases" / "test_meters.db")
)
ENV_DATA_DB_PATH = os.environ.get(
    "ENV_DATA_DB_PATH",
    str(BASE_DIR / "overhaul" / "databases" / "test_envdata.db")
)

# FAISS index and metadata
FAISS_INDEX_PATH = os.environ.get(
    "FAISS_INDEX_PATH",
    str(BASE_DIR / "overhaul" / "faiss_index.idx")
)
FAISS_META_PATH = os.environ.get(
    "FAISS_META_PATH",
    str(BASE_DIR / "overhaul" / "faiss_metadata.pkl")
)

# Output directory
OUTPUT_DIR = os.environ.get(
    "OUTPUT_DIR",
    str(BASE_DIR / "overhaul" / "outputs")
)

# Example file (for tests, etc.)
EXAMPLE_PDF_PATH = os.environ.get(
    "EXAMPLE_PDF_PATH",
    str(BASE_DIR / "overhaul" / "examples" / "redacted_output.pdf")
)

# Add more config variables as needed
