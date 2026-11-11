import asyncio
import logging
import shutil
from collections.abc import Awaitable, Callable
from concurrent.futures import Future

import discord

import config
from playback.errors import ResolveError
from playback.queue import MusicQueue
from playback.resolver import resolve_stream_url
from playback.track import Track

log = logging.getLogger(__name__)

STREAM_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffmpeg_kwargs(track: Track) -> dict[str, str]:
    if track.is_local:
        return {"options": FFMPEG_OPTIONS}
    return {"before_options": STREAM_BEFORE_OPTIONS, "options": FFMPEG_OPTIONS}


class GuildPlayer:
    def __init__(
        self,
        voice_client: discord.VoiceClient,
        queue: MusicQueue,
        get_volume_percent: Callable[[], Awaitable[int]],
        idle_timeout_seconds: float,
    ) -> None:
        self.voice_client = voice_client
        self.queue = queue
        self._get_volume_percent = get_volume_percent
        self._idle_timeout_seconds = idle_timeout_seconds
        self._loop = asyncio.get_running_loop()
        self._lock = asyncio.Lock()
        self._idle_task: asyncio.Task | None = None
        self._closed = False

    @property
    def is_active(self) -> bool:
        return self.voice_client.is_playing() or self.voice_client.is_paused()

    async def start_if_idle(self) -> None:
        async with self._lock:
            if not self.is_active and not self._closed:
                await self._play_next()

    def pause(self) -> None:
        self.voice_client.pause()

    def resume(self) -> None:
        self.voice_client.resume()

    def skip(self) -> None:
        self.voice_client.stop()

    def stop(self) -> None:
        self.queue.clear()
        self.voice_client.stop()

    async def disconnect(self) -> None:
        self._closed = True
        self._cancel_idle_timer()
        self.queue.clear()
        await self.voice_client.disconnect()

    async def _play_next(self) -> None:
        self._cancel_idle_timer()
        while (track := self.queue.advance()) is not None:
            try:
                stream_url = await resolve_stream_url(track)
                source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_kwargs(track))
            except ResolveError:
                continue
            except discord.ClientException:
                log.exception("Could not start FFmpeg for '%s'", track.title)
                continue
            volume = await self._get_volume_percent() / config.MAX_VOLUME_PERCENT
            self.voice_client.play(
                discord.PCMVolumeTransformer(source, volume=volume), after=self._on_track_end
            )
            return
        self._idle_task = self._loop.create_task(self._disconnect_when_idle())

    def _on_track_end(self, error: Exception | None) -> None:
        if error is not None:
            log.error("Playback error", exc_info=error)
        future = asyncio.run_coroutine_threadsafe(self.start_if_idle(), self._loop)
        future.add_done_callback(_log_failure)

    async def _disconnect_when_idle(self) -> None:
        await asyncio.sleep(self._idle_timeout_seconds)
        log.info("Leaving %s after being idle", self.voice_client.channel)
        self._idle_task = None
        await self.disconnect()

    def _cancel_idle_timer(self) -> None:
        if self._idle_task is not None:
            self._idle_task.cancel()
            self._idle_task = None


def _log_failure(future: Future) -> None:
    error = future.exception()
    if error is not None:
        log.error("Failed to advance the queue", exc_info=error)
