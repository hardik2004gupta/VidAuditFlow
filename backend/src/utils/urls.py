"""Small, dependency-free URL helpers shared across the backend.

Kept separate from ``services/`` so this logic has no dependency on
``core.config`` or any Azure SDK and can be unit tested (and reused by a
future API-level validator) in isolation.
"""

from __future__ import annotations

_SUPPORTED_VIDEO_HOSTS = ("youtube.com", "youtu.be")


def is_supported_video_url(url: str) -> bool:
    """Return True if ``url`` looks like a YouTube URL.

    This intentionally preserves the original substring-based check rather
    than tightening it to strict host parsing. TECHNICAL_DEBT.md (TD-13)
    tracks upgrading this to a real URL-parse + host allow-list check as a
    later, dedicated phase -- this phase only relocates the existing logic.
    """
    return any(host in url for host in _SUPPORTED_VIDEO_HOSTS)
