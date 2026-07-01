"""YouTube video download service.

Extracted out of ``video_indexer.py`` (which now only talks to the Azure
Video Indexer REST API) so each service module has a single external
responsibility -- see FOLDER_STRUCTURE_V2.md.

``yt-dlp`` is a synchronous library with no native asyncio API, so the
actual download runs in a worker thread via ``asyncio.to_thread`` and is
awaited from here -- this is what makes the download non-blocking for the
FastAPI event loop (PROJECT_AUDIT.md finding C1 / M1).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import yt_dlp

from backend.src.core.exceptions import VideoDownloadError
from backend.src.core.logging import get_logger
from backend.src.utils.urls import is_supported_video_url

logger = get_logger(__name__)

DEFAULT_VIDEO_FILENAME = "source_video.mp4"


async def download_youtube_video(
    video_url: str,
    output_dir: Path,
    filename: str = DEFAULT_VIDEO_FILENAME,
) -> Path:
    """Download ``video_url`` into ``output_dir`` and return the local file path.

    ``output_dir`` should be a per-job temporary directory (see
    ``graph/nodes.py``) so concurrent audits never share a filename --
    closing PROJECT_AUDIT.md finding C3.

    Raises:
        VideoDownloadError: if the URL isn't a recognized YouTube URL, or if
            the download itself fails.
    """
    if not is_supported_video_url(video_url):
        raise VideoDownloadError("Please provide a valid YouTube URL for this test.")

    output_path = output_dir / filename
    logger.info("Downloading YouTube video", extra={"video_url": video_url})

    ydl_opts = {
        "format": "best",
        "outtmpl": str(output_path),
        "quiet": False,
        "no_warnings": False,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    }

    def _run_download() -> None:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

    try:
        # yt-dlp is blocking; run it off the event loop.
        await asyncio.to_thread(_run_download)
    except Exception as exc:  # yt-dlp raises its own broad exception types
        raise VideoDownloadError(f"YouTube download failed: {exc}") from exc

    logger.info("Download complete", extra={"output_path": str(output_path)})
    return output_path
