"""Shared pytest fixtures for the backend test suite.

Sets required-but-dummy environment variables *before* anything under
``backend.src`` is imported, so ``core.config.get_settings()`` (which is
``@lru_cache``d -- first import wins for the whole process) never needs
real Azure credentials or a developer's local ``.env`` to run. Explicit
``os.environ[...]`` assignment (not ``setdefault``) takes precedence over
whatever pydantic-settings would otherwise read from a real ``.env`` file,
so tests are hermetic regardless of what's in the local checkout.

No test in this suite makes a real network call to Azure OpenAI, Azure AI
Search, or Azure Video Indexer -- every LLM/vector-store touchpoint is
mocked at the ``graph.llm_clients``/``services.report_chat`` boundary (see
the ``mock_chat_llm`` fixture below and its use in individual test files).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import AsyncIterator, Iterator
from uuid import uuid4

_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="vidauditflow-test-"))
_TEST_DB_PATH = _TEST_DB_DIR / "test.db"

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com"
os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"] = "test-chat-deployment"
os.environ["AZURE_SEARCH_ENDPOINT"] = "https://test.search.windows.net"
os.environ["AZURE_SEARCH_API_KEY"] = "test-search-key"
os.environ["AZURE_SEARCH_INDEX_NAME"] = "test-index"
os.environ["AZURE_VI_LOCATION"] = "eastus"
os.environ["AZURE_VI_ACCOUNT_ID"] = "00000000-0000-0000-0000-000000000000"
os.environ["AZURE_SUBSCRIPTION_ID"] = "00000000-0000-0000-0000-000000000000"
os.environ["AZURE_RESOURCE_GROUP"] = "test-rg"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:3000"

# `api/main.py` calls `load_dotenv(override=True)` at import time, which
# would clobber the dummy values just set above with whatever's in a real
# local `.env` (even empty-string values, since `override=True` replaces
# unconditionally) -- making tests non-hermetic and dependent on what a
# given developer's machine happens to have on disk. No-op it before that
# import can run.
import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *args, **kwargs: False

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from backend.src.api.main import app  # noqa: E402
from backend.src.db.session import AsyncSessionFactory, engine  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_test_schema() -> AsyncIterator[None]:
    """Create every table once for the whole test session (no Alembic involved)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A real database session against the test SQLite file, one per test."""
    async with AsyncSessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An async HTTP client wired directly to the FastAPI app (no real server)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def video_id() -> str:
    return f"vid_{uuid4().hex[:8]}"
