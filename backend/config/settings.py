"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from backend.config.constants import (
    DEFAULT_DASHSCOPE_BASE_URL,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_TIMEOUT_SECONDS,
    DEFAULT_QWEN_MAX_TOKENS,
    DEFAULT_QWEN_MODEL,
    DEFAULT_QWEN_TEMPERATURE,
    DEFAULT_QWEN_TIMEOUT_SECONDS,
)


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for API, storage, queues, and model integrations."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / "..env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "MasonGraphRAG"
    DEV_MODE: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DASHSCOPE_API_KEY: str | None = None
    DASHSCOPE_BASE_URL: str = DEFAULT_DASHSCOPE_BASE_URL
    QWEN_API_KEY: str | None = None
    QWEN_BASE_URL: str | None = None
    QWEN_MODEL: str = DEFAULT_QWEN_MODEL
    QWEN_TEMPERATURE: float = DEFAULT_QWEN_TEMPERATURE
    QWEN_MAX_TOKENS: int = DEFAULT_QWEN_MAX_TOKENS
    QWEN_TIMEOUT_SECONDS: int = DEFAULT_QWEN_TIMEOUT_SECONDS

    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_MODEL: str = DEFAULT_EMBEDDING_MODEL
    EMBEDDING_DIMENSION: int = DEFAULT_EMBEDDING_DIMENSION
    EMBEDDING_TIMEOUT_SECONDS: int = DEFAULT_EMBEDDING_TIMEOUT_SECONDS

    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'backend/data/state/mason_graph_rag.db').as_posix()}"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = True

    MINIO_ENABLED: bool = False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "mason-knowledge"
    MINIO_SECURE: bool = False

    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    DOCUMENT_STORAGE_DIR: str = "backend/data/uploads"
    DOCUMENT_INDEX_FILE: str = "backend/data/state/documents.json"
    KNOWLEDGE_BASE_SETTINGS_FILE: str = "backend/data/state/knowledge_base_settings.json"

    ENABLE_ADVANCED_GRAPHRAG: bool = True
    ENABLE_DEBUG_TRACES: bool = True
    ENABLE_ASYNC_INGESTION: bool = True
    ENABLE_EVALUATION: bool = True

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def document_storage_dir(self) -> Path:
        return ROOT_DIR / self.DOCUMENT_STORAGE_DIR

    @property
    def document_index_file(self) -> Path:
        return ROOT_DIR / self.DOCUMENT_INDEX_FILE

    @property
    def knowledge_base_settings_file(self) -> Path:
        return ROOT_DIR / self.KNOWLEDGE_BASE_SETTINGS_FILE

    @property
    def resolved_qwen_api_key(self) -> str | None:
        return self.QWEN_API_KEY or self.DASHSCOPE_API_KEY

    @property
    def resolved_qwen_base_url(self) -> str:
        return self.QWEN_BASE_URL or self.DASHSCOPE_BASE_URL

    @property
    def resolved_embedding_api_key(self) -> str | None:
        return self.EMBEDDING_API_KEY or self.DASHSCOPE_API_KEY

    @property
    def resolved_embedding_base_url(self) -> str:
        return self.EMBEDDING_BASE_URL or self.DASHSCOPE_BASE_URL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
