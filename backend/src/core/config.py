"""Central application configuration.

This module is the ONLY place in the backend that reads environment
variables. Every other module must import ``settings`` from here instead of
calling ``os.getenv`` directly.

Centralizing configuration this way fixes two problems identified in
PROJECT_AUDIT.md / TECHNICAL_DEBT.md:

- TD-15 (M2): the Azure OpenAI embedding deployment name was hardcoded in
  ``graph/nodes.py`` and independently defaulted in
  ``scripts/index_documents.py``, so the two could silently drift apart.
  There is now exactly one default, defined once, used everywhere.
- Inconsistent "required vs. optional with a default" handling across env
  vars (e.g. ``AZURE_VI_NAME`` had a code default while
  ``AZURE_OPENAI_API_VERSION`` did not). Every setting below has an
  explicit, intentional default (or none, if it is truly required).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.src.core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Typed, validated application settings loaded from the environment/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App metadata ---
    environment: str = "local"
    app_name: str = "VidAuditFlow API"
    app_version: str = "0.2.0"

    # --- Azure OpenAI (required: the compliance pipeline cannot run without these) ---
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_chat_deployment: str
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # --- Azure AI Search (RAG knowledge base) ---
    azure_search_endpoint: str
    azure_search_api_key: str
    azure_search_index_name: str

    # --- Azure Video Indexer ---
    azure_vi_name: str = "project-brand-guardian-001"
    azure_vi_location: str
    azure_vi_account_id: str
    azure_subscription_id: str
    azure_resource_group: str

    # --- Azure Storage (reserved; not yet used by any code path) ---
    azure_storage_connection_string: Optional[str] = None

    # --- Observability (both optional; features degrade gracefully if unset) ---
    applicationinsights_connection_string: Optional[str] = None
    langchain_tracing_v2: Optional[str] = None
    langchain_endpoint: Optional[str] = None
    langchain_api_key: Optional[str] = None
    langchain_project: Optional[str] = None

    # --- HTTP / reliability tuning ---
    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3
    video_indexer_poll_interval_seconds: float = 30.0
    video_indexer_max_poll_attempts: int = 60  # ~30 minutes ceiling before giving up


@lru_cache
def get_settings() -> Settings:
    """Build (and cache) the process-wide :class:`Settings` instance.

    Fails fast with a clear :class:`ConfigurationError` if required
    variables are missing, instead of letting a downstream Azure SDK call
    fail with a confusing error deep inside a graph node.
    """
    try:
        return Settings()
    except PydanticValidationError as exc:
        raise ConfigurationError(f"Invalid or missing configuration: {exc}") from exc


settings = get_settings()
