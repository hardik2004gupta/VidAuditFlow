"""LangGraph state schema for the video compliance audit workflow."""

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from backend.src.schemas.audit import ComplianceIssue

__all__ = ["VideoAuditState", "ComplianceIssue"]


class VideoAuditState(TypedDict):
    """The data schema shared across every node in the LangGraph execution."""

    # --- Input Parameters ---
    video_url: str
    video_id: str

    # --- Ingestion & Extraction Data ---
    # Optional because they are populated asynchronously by the Indexer Node.
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]  # e.g., {"duration": 15, "resolution": "1080p"}
    transcript: Optional[str]       # Full extracted speech-to-text
    ocr_text: List[str]             # List of recognized on-screen text

    # --- Analysis Output ---
    # Annotated with operator.add so multiple nodes can append without
    # overwriting each other's contributions.
    compliance_results: Annotated[List[ComplianceIssue], operator.add]

    # --- Final Deliverables ---
    final_status: str               # "PASS" | "FAIL"
    final_report: str               # Markdown summary for the frontend

    # --- System Observability ---
    # Appends system-level errors (e.g., API timeouts) without halting execution logic.
    errors: Annotated[List[str], operator.add]
