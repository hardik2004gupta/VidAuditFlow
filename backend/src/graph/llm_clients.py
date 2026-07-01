"""Cached factory functions for the Azure OpenAI / Azure AI Search clients.

Stabilization fix (Phase 4.5): ``retrieval_agent``, ``compliance_agent``,
and ``summary_agent`` each independently constructed a fresh
``AzureChatOpenAI``/``AzureOpenAIEmbeddings``/``AzureSearch`` client on
*every* node invocation, with near-identical arguments. BACKEND_VISION.md's
Dependency Injection section is explicit that stateless API clients like
these "are constructed once at startup and injected as singletons," not
rebuilt per call -- this module is that single construction point,
following the exact same ``@lru_cache`` pattern ``core/config.py``'s
``get_settings()`` already uses.

These clients hold no per-call state (safe to reuse across concurrent
node invocations) and never bind to a specific asyncio event loop at
construction time, so caching them at module scope is safe.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from backend.src.core.config import settings


@lru_cache
def get_chat_llm(temperature: float) -> AzureChatOpenAI:
    """Return a cached ``AzureChatOpenAI`` client for the given temperature.

    Cached per-temperature since the Compliance Agent (temperature=0.0,
    deterministic judgments) and the Summary Agent (temperature=0.3,
    narrative writing) intentionally use different settings.
    """
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_chat_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        openai_api_version=settings.azure_openai_api_version,
        temperature=temperature,
    )


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    """Return the cached ``AzureOpenAIEmbeddings`` client."""
    return AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        openai_api_version=settings.azure_openai_api_version,
    )


@lru_cache
def get_vector_store() -> AzureSearch:
    """Return the cached ``AzureSearch`` vector store client."""
    return AzureSearch(
        azure_search_endpoint=settings.azure_search_endpoint,
        azure_search_key=settings.azure_search_api_key,
        index_name=settings.azure_search_index_name,
        embedding_function=get_embeddings().embed_query,
    )
