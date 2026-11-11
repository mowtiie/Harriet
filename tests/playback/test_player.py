"""Tests for the per-server player using a fake voice client."""

import unittest
from unittest import mock

from playback.player import GuildPlayer, ffmpeg_kwargs
from playback.queue import MusicQueue
from playback.track import Track


class FakeVoiceClient:
    def __init__(self) -> None:
        self.played: list[object] = []
        self.playing = False
        self.paused = False
        self.disconnected = False
        self.channel = "voice"
        self.voice_privacy_code = None

    def is_playing(self) -> bool:
        return self.playing

    def is_paused(self) -> bool:
        return self.paused

    def play(self, source: object, after: object = None) -> None:
        self.played.append(source)
        self.playing = True

    def stop(self) -> None:
        self.playing = False

    async def disconnect(self) -> None:
        self.disconnected = True


def local_track(title: str) -> Track:
    return Track(title, f"/music/{title}.mp3", True, None, "tester")


async def fixed_volume() -> int:
    return 50


class FfmpegKwargsTests(unittest.TestCase):
    def test_streams_reconnect_but_local_files_do_not(self) -> None:
        self.assertIn("before_options", ffmpeg_kwargs(Track("t", "https://x", False, 1, "u")))
        self.assertNotIn("before_options", ffmpeg_kwargs(local_track("a")))


class GuildPlayerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.voice = FakeVoiceClient()
        self.queue = MusicQueue(max_size=5)
        self.player = GuildPlayer(self.voice, self.queue, fixed_volume, idle_timeout_seconds=60)
        ffmpeg_patcher = mock.patch("playback.player.discord.FFmpegPCMAudio")
        self.ffmpeg = ffmpeg_patcher.start()
        self.addCleanup(ffmpeg_patcher.stop)
        transformer_patcher = mock.patch("playback.player.discord.PCMVolumeTransformer")
        self.transformer = transformer_patcher.start()
        self.addCleanup(transformer_patcher.stop)

    async def asyncTearDown(self) -> None:
        self.player._cancel_idle_timer()

    async def test_starts_first_track_with_configured_volume(self) -> None:
        track = local_track("a")
        self.queue.add(track)
        await self.player.start_if_idle()
        self.ffmpeg.assert_called_once_with(track.source, options="-vn")
        self.assertEqual(self.transformer.call_args.kwargs["volume"], 0.5)
        self.assertIs(self.queue.current, track)

    async def test_does_not_interrupt_a_playing_track(self) -> None:
        self.queue.add(local_track("a"))
        self.queue.add(local_track("b"))
        await self.player.start_if_idle()
        await self.player.start_if_idle()
        self.assertEqual(len(self.voice.played), 1)

    async def test_stop_clears_the_queue(self) -> None:
        self.queue.add(local_track("a"))
        self.queue.add(local_track("b"))
        await self.player.start_if_idle()
        self.player.stop()
        self.assertIsNone(self.queue.current)
        self.assertEqual(self.queue.upcoming, ())
        self.assertFalse(self.voice.playing)

    async def test_empty_queue_schedules_idle_disconnect(self) -> None:
        await self.player.start_if_idle()
        self.assertIsNotNone(self.player._idle_task)

    async def test_disconnect_closes_the_player(self) -> None:
        await self.player.disconnect()
        self.assertTrue(self.voice.disconnected)
        self.queue.add(local_track("a"))
        await self.player.start_if_idle()
        self.assertEqual(self.voice.played, [])


if __name__ == "__main__":
    unittest.main()
