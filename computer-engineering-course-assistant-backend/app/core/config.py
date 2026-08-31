from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "computer-engineering-course-assistant")
    database_path: Path = Path(
        os.getenv("DATABASE_PATH", str(BACKEND_ROOT / "data" / "assistant.db"))
    )
    document_storage_path: Path = Path(
        os.getenv("DOCUMENT_STORAGE_PATH", str(BACKEND_ROOT / "data" / "documents"))
    )

    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "qwen3-embedding-0.6b"
    )
    chat_model_name: str = os.getenv("CHAT_MODEL_NAME", "qwen3-4b")

    # Foundry Local's Python SDK defaults to a per-app_name cache directory
    # (~/.{app_name}/cache/models) that is separate from the Foundry CLI's
    # own cache (~/.foundry/cache/models, see `foundry cache location`).
    # Pointing the SDK at the CLI's cache root lets the backend see models
    # already downloaded via the CLI without downloading them a second time.
    foundry_model_cache_dir: Path = Path(
        os.getenv(
            "FOUNDRY_MODEL_CACHE_DIR",
            str(Path.home() / ".foundry" / "cache" / "models"),
        )
    )

    top_k: int = int(os.getenv("TOP_K", "3"))
    min_similarity_score: float = float(os.getenv("MIN_SIMILARITY_SCORE", "0.30"))
    # Max characters per chunk for the paragraph-aware chunker (see
    # chunking_service.chunk_text). Chosen experimentally: small enough that
    # a chunk usually holds one sub-topic (not the whole multi-topic page a
    # naive paragraph-count-based split could produce), large enough to
    # rarely split a single section across chunks. See chunking_service
    # module for the reasoning.
    chunk_max_chars: int = int(os.getenv("CHUNK_MAX_CHARS", "1000"))

    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    auto_download_models: bool = _env_bool("AUTO_DOWNLOAD_MODELS", True)

    frontend_origins_raw: str = os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173"
    )

    chat_temperature: float = float(os.getenv("CHAT_TEMPERATURE", "0.2"))
    chat_max_tokens: int = int(os.getenv("CHAT_MAX_TOKENS", "700"))

    @property
    def frontend_origins(self) -> list[str]:
        return [
            item.strip()
            for item in self.frontend_origins_raw.split(",")
            if item.strip()
        ]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
