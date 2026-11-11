import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

from playback.errors import ResolveError
from playback.track import Track

log = logging.getLogger(__name__)

WEB_SCHEMES = ("http", "https")
SEARCH_PREFIX = "ytsearch1:"
YTDLP_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}


def is_web_url(query: str) -> bool:
    return urlparse(query).scheme in WEB_SCHEMES


def find_local_file(query: str, music_dir: Path) -> Path | None:
    """Matches direct children only, so a query can never escape the music folder."""
    wanted = query.strip().lower()
    return next(
        (path for path in _local_files(music_dir) if wanted in (path.name.lower(), path.stem.lower())),
        None,
    )


def matching_local_names(music_dir: Path, current: str, limit: int) -> list[str]:
    needle = current.strip().lower()
    names = sorted(path.name for path in _local_files(music_dir))
    return [name for name in names if needle in name.lower()][:limit]


def _local_files(music_dir: Path) -> list[Path]:
    if not music_dir.is_dir():
        return []
    return [path for path in music_dir.iterdir() if path.is_file()]


async def resolve_track(query: str, music_dir: Path, requested_by: str) -> Track:
    local = None if is_web_url(query) else find_local_file(query, music_dir)
    if local is not None:
        return Track(local.stem, str(local), True, None, requested_by)

    search_term = query if is_web_url(query) else f"{SEARCH_PREFIX}{query}"
    info = await _extract(search_term)
    entry = info["entries"][0] if info.get("entries") else info
    return Track(
        title=entry.get("title", "Unknown title"),
        source=entry.get("webpage_url") or entry["url"],
        is_local=False,
        duration_seconds=_whole_seconds(entry.get("duration")),
        requested_by=requested_by,
    )


async def resolve_stream_url(track: Track) -> str:
    if track.is_local:
        return track.source
    info = await _extract(track.source)
    return info["url"]


def _whole_seconds(duration: float | None) -> int | None:
    return None if duration is None else int(duration)


async def _extract(term: str) -> dict:
    try:
        return await asyncio.to_thread(_extract_blocking, term)
    except (yt_dlp.utils.DownloadError, KeyError, IndexError) as error:
        log.warning("Could not resolve %r", term, exc_info=error)
        raise ResolveError(f"Could not find anything playable for `{term}`.") from error


def _extract_blocking(term: str) -> dict:
    with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        info = ydl.extract_info(term, download=False)
    if info is None:
        raise KeyError(term)
    return info
