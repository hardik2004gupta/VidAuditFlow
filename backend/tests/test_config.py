"""core.config.Settings -- loading, defaults, and the CORS list parser.

conftest.py sets every required env var (and no-ops `load_dotenv`) before
anything under backend.src is imported, so `get_settings()` -- an
`@lru_cache`d singleton -- reflects those dummy values for the whole test
session; `test_required_settings_loaded_from_environment` and the CORS
tests check that singleton directly.

Field *defaults*, however, can't be checked on that shared singleton: a
real local `.env` file's `env_file=".env"` config on `Settings` is read by
pydantic-settings' own internal loader (independent of the `load_dotenv`
patch), so an optional field a developer's `.env` happens to set -- even to
an empty string -- would silently shadow its class default there. Those
tests instead build a fully isolated `Settings(..., _env_file=None)`
instance via `_fresh_settings()` below.
"""

from __future__ import annotations

from backend.src.core.config import Settings, settings

_REQUIRED_FIELDS = dict(
    azure_openai_api_key="k",
    azure_openai_endpoint="https://x",
    azure_openai_chat_deployment="d",
    azure_search_endpoint="https://x",
    azure_search_api_key="k",
    azure_search_index_name="i",
    azure_vi_location="eastus",
    azure_vi_account_id="a",
    azure_subscription_id="s",
    azure_resource_group="r",
)


def _fresh_settings(monkeypatch, **overrides: object) -> Settings:
    """A `Settings` instance isolated from both the test-session env vars and any real local `.env`."""
    for key in ("DATABASE_URL", "AZURE_OPENAI_API_VERSION", "HTTP_MAX_RETRIES", "HTTP_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)
    return Settings(**_REQUIRED_FIELDS, _env_file=None, **overrides)


def test_required_settings_loaded_from_environment() -> None:
    assert settings.azure_openai_api_key == "test-key"
    assert settings.azure_openai_endpoint == "https://test.openai.azure.com"
    assert settings.azure_search_index_name == "test-index"


def test_optional_settings_have_sensible_defaults(monkeypatch) -> None:
    fresh = _fresh_settings(monkeypatch)
    assert fresh.azure_openai_api_version == "2024-02-01"
    assert fresh.azure_openai_embedding_deployment == "text-embedding-3-small"
    assert fresh.http_max_retries == 3
    assert fresh.http_timeout_seconds == 30.0
    assert fresh.database_url == "sqlite+aiosqlite:///./vidauditflow.db"


def test_cors_allowed_origins_list_splits_and_trims() -> None:
    assert settings.cors_allowed_origins == "http://localhost:3000"
    assert settings.cors_allowed_origins_list == ["http://localhost:3000"]


def test_cors_allowed_origins_list_handles_multiple_and_whitespace() -> None:
    multi = Settings(cors_allowed_origins=" http://localhost:3000 , https://example.com ,,")
    assert multi.cors_allowed_origins_list == ["http://localhost:3000", "https://example.com"]
