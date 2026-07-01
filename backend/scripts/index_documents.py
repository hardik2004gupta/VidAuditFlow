"""Offline ingestion script: reads PDFs from backend/data, chunks them, and
uploads embeddings to Azure AI Search.

Run from the repo root with:

    uv run python backend/scripts/index_documents.py

This is an operator-run, one-off tool -- it is never imported by the running
application (see FOLDER_STRUCTURE_V2.md). It still reads its configuration
through ``core.config.settings`` (via the small ``sys.path`` bootstrap
below) rather than its own independent ``os.getenv`` calls, so the embedding
deployment name it uses to build the index can never drift from the one the
Auditor node uses to query it -- this was previously a real bug
(TECHNICAL_DEBT.md TD-15 / audit finding M2): this script defaulted to
``text-embedding-3-small`` for the *index*, while ``graph/nodes.py``
independently hardcoded the same string for the *query*. Two independent
copies of the same default is exactly how they eventually drift.
"""

import glob
import os
import sys
from pathlib import Path

# Make `backend.src.*` importable regardless of how this script is invoked
# (`python backend/scripts/index_documents.py`, `python -m backend.scripts.
# index_documents`, or via `uv run`).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader  # noqa: E402
from langchain_community.vectorstores import AzureSearch  # noqa: E402
from langchain_openai import AzureOpenAIEmbeddings  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

from backend.src.core.config import settings  # noqa: E402
from backend.src.core.logging import get_logger  # noqa: E402

logger = get_logger("indexer-script")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def index_docs() -> None:
    """Reads PDFs from backend/data, chunks them, and uploads vectors to Azure AI Search."""
    data_folder = _REPO_ROOT / "backend" / "data"

    logger.info("=" * 60)
    logger.info("Environment Configuration Check:")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {settings.azure_openai_endpoint}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {settings.azure_openai_api_version}")
    logger.info(f"Embedding Deployment: {settings.azure_openai_embedding_deployment}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {settings.azure_search_endpoint}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {settings.azure_search_index_name}")
    logger.info("=" * 60)

    try:
        logger.info("Initializing Azure OpenAI Embeddings...")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.azure_openai_embedding_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            openai_api_version=settings.azure_openai_api_version,
        )
        logger.info("Embeddings model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {e}")
        logger.error("Please verify your Azure OpenAI deployment name and endpoint.")
        return

    try:
        logger.info("Initializing Azure AI Search vector store...")
        index_name = settings.azure_search_index_name
        vector_store = AzureSearch(
            azure_search_endpoint=settings.azure_search_endpoint,
            azure_search_key=settings.azure_search_api_key,
            index_name=index_name,
            embedding_function=embeddings.embed_query,
        )
        logger.info(f"Vector store initialized for index: {index_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search: {e}")
        logger.error("Please verify your Azure Search endpoint, API key, and index name.")
        return

    pdf_files = glob.glob(os.path.join(str(data_folder), "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {data_folder}. Please add files.")
        return

    logger.info(f"Found {len(pdf_files)} PDFs to process: {[os.path.basename(f) for f in pdf_files]}")

    all_splits = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading: {os.path.basename(pdf_path)}...")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            # Split text into 1000-character chunks with 200-character overlap
            # so context isn't lost between cuts.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )
            splits = text_splitter.split_documents(raw_docs)

            # Tag the source for citation later.
            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f" -> Split into {len(splits)} chunks.")

        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")

    if all_splits:
        logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search Index '{index_name}'...")
        try:
            vector_store.add_documents(documents=all_splits)
            logger.info("=" * 60)
            logger.info("Indexing Complete! The Knowledge Base is ready.")
            logger.info(f"Total chunks indexed: {len(all_splits)}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"Failed to upload documents to Azure Search: {e}")
            logger.error("Please check your Azure Search configuration and try again.")
    else:
        logger.warning("No documents were processed.")


if __name__ == "__main__":
    index_docs()
