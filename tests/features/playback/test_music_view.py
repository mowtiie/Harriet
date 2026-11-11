"""Tests for music text formatting."""

import unittest

from features.playback.music_view import (
    MAX_QUEUE_LINES,
    format_queue_line,
    format_track,
    format_upcoming,
)
from features.playback.track import Track


def make_track(title: str, duration: int | None = 185) -> Track:
    return Track(title, "https://example.com", False, duration, "Sam")


class FormatTrackTests(unittest.TestCase):
    def test_shows_title_duration_and_requester(self) -> None:
        self.assertEqual(format_track(make_track("Song")), "**Song**\n-# 3:05 · requested by Sam")


class FormatUpcomingTests(unittest.TestCase):
    def test_empty_queue(self) -> None:
        self.assertEqual(format_upcoming([]), "Nothing queued.")

    def test_numbers_each_track(self) -> None:
        self.assertEqual(format_queue_line(2, make_track("Song", None)), "`2.` Song · Live")

    def test_truncates_long_queues(self) -> None:
        tracks = [make_track(f"t{i}") for i in range(MAX_QUEUE_LINES + 3)]
        lines = format_upcoming(tracks).splitlines()
        self.assertEqual(len(lines), MAX_QUEUE_LINES + 1)
        self.assertEqual(lines[-1], "-# and 3 more")


if __name__ == "__main__":
    unittest.main()
