"""Application-specific exceptions.

Raising one of these (instead of a bare ``Exception``) lets callers tell
"this specific pipeline step failed" apart from an unexpected bug, and lets
the API layer map failures to meaningful HTTP responses instead of leaking
raw internal error text to clients.
"""

from __future__ import annotations


class VidAuditFlowError(Exception):
    """Base class for every application-raised error in VidAuditFlow."""


class ConfigurationError(VidAuditFlowError):
    """Required configuration (env vars/settings) is missing or invalid."""


class VideoDownloadError(VidAuditFlowError):
    """Downloading the source video (e.g. via yt-dlp) failed."""


class VideoIndexerError(VidAuditFlowError):
    """Azure Video Indexer upload, polling, or extraction failed."""


class RetrievalError(VidAuditFlowError):
    """Retrieving relevant policy chunks from Azure AI Search failed."""


class ComplianceError(VidAuditFlowError):
    """The compliance LLM call failed or returned an unusable response."""


class ValidationError(VidAuditFlowError):
    """An input failed a domain-level validation rule."""


class NotFoundError(VidAuditFlowError):
    """A requested resource (job, report, ...) does not exist."""
