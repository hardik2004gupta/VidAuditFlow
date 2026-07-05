"""graph.state.VideoAuditState -- the Pydantic model shared across every LangGraph node.

Doesn't exercise the graph itself (out of scope: "Do NOT change LangGraph"
extends to not needing to re-test its internals here) -- just the state
schema's own validation and reducer-related invariants, since a mistake
here (e.g. an accumulating field losing its `operator.add` annotation)
would silently corrupt every node's view of prior progress.
"""

from __future__ import annotations

import operator

import pytest
from pydantic import ValidationError

from backend.src.graph.state import VideoAuditState


def test_state_requires_video_url_and_video_id() -> None:
    state = VideoAuditState(video_url="https://youtu.be/abc123", video_id="vid_abc123")
    assert state.video_url == "https://youtu.be/abc123"
    assert state.video_id == "vid_abc123"


def test_state_missing_required_fields_raises() -> None:
    with pytest.raises(ValidationError):
        VideoAuditState()  # type: ignore[call-arg]


def test_state_defaults_are_empty_and_pending() -> None:
    state = VideoAuditState(video_url="https://youtu.be/abc123", video_id="vid_abc123")
    assert state.transcript is None
    assert state.transcript_status == "pending"
    assert state.ocr_text == []
    assert state.violations == []
    assert state.job_status == "pending"
    assert state.warnings == []
    assert state.errors == []
    assert state.processing_metadata == []


@pytest.mark.parametrize(
    "field_name",
    ["violations", "warnings", "errors", "processing_metadata"],
)
def test_accumulating_fields_are_annotated_with_operator_add(field_name: str) -> None:
    """These fields must stay `operator.add`-annotated or partial node
    updates would overwrite prior progress instead of appending to it --
    exactly the bug `jobs/audit_runner.py`'s `_accumulating_fields()` helper
    exists to never silently drift out of sync with."""
    field_info = VideoAuditState.model_fields[field_name]
    assert operator.add in field_info.metadata


def test_non_accumulating_fields_are_not_annotated_with_operator_add() -> None:
    for field_name in ("transcript", "confidence_score", "job_status", "video_url"):
        field_info = VideoAuditState.model_fields[field_name]
        assert operator.add not in field_info.metadata
