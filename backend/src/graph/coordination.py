"""Single-flight coordination for work shared between parallel graph nodes.

The Transcript Agent and OCR Agent run as true concurrent LangGraph branches
(see ``graph/workflow.py``), but Azure Video Indexer returns transcript and
OCR insights from a *single* indexing job. Both agents need that one
response; neither may trigger its own independent download/upload/poll
cycle, or the pipeline would pay for (and wait through) the expensive Azure
Video Indexer step twice per audit -- exactly the "duplicate indexing work"
AI_PIPELINE_VISION.md rules out.

:class:`SingleFlightGroup` solves this without a persistent cache: whichever
of the two agents calls :meth:`SingleFlightGroup.run` first actually
performs the fetch; the other awaits the *same* in-flight ``asyncio.Task``
and gets the same result (or the same exception) once it completes. Each
job's entry is removed as soon as both expected callers have observed the
result, so nothing here persists beyond the lifetime of one audit -- this is
per-job request coalescing, not a cache (the DO NOT IMPLEMENT list for this
phase excludes caching as a feature; this is a concurrency-correctness
primitive scoped to a single graph run, not a store of reusable results for
future, unrelated requests).
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Dict, TypeVar

T = TypeVar("T")


class SingleFlightGroup:
    """Coalesces concurrent callers for the same key onto one coroutine call."""

    def __init__(self) -> None:
        self._tasks: Dict[str, "asyncio.Task"] = {}
        self._pending_callers: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def run(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        """Run ``factory()`` for ``key`` at most once concurrently.

        If another caller already started a fetch for the same ``key``,
        this awaits that call's result instead of starting a new one.
        """
        async with self._lock:
            task = self._tasks.get(key)
            if task is None:
                task = asyncio.ensure_future(factory())
                self._tasks[key] = task
                self._pending_callers[key] = 0
            self._pending_callers[key] += 1

        try:
            return await task
        finally:
            async with self._lock:
                self._pending_callers[key] -= 1
                if self._pending_callers[key] <= 0:
                    self._tasks.pop(key, None)
                    self._pending_callers.pop(key, None)


# Process-wide instance. Safe to share across concurrent, unrelated audits
# because every call is keyed by that audit's unique job/video id -- two
# different jobs never coalesce onto each other's fetch.
video_indexer_fetch_group = SingleFlightGroup()
