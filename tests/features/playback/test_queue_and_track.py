"""Tests for the track model and queue."""

import unittest

from features.playback.errors import QueueFullError
from features.playback.queue import MusicQueue
from features.playback.track import Track, format_duration


def make_track(title: str) -> Track:
    return Track(title, f"https://example.com/{title}", False, 60, "tester")


class FormatDurationTests(unittest.TestCase):
    def test_formats_minutes_and_seconds(self) -> None:
        self.assertEqual(format_duration(5), "0:05")
        self.assertEqual(format_duration(185), "3:05")

    def test_formats_hours(self) -> None:
        self.assertEqual(format_duration(3725), "1:02:05")

    def test_none_means_live(self) -> None:
        self.assertEqual(format_duration(None), "Live")


class MusicQueueTests(unittest.TestCase):
    def test_add_returns_position(self) -> None:
        queue = MusicQueue(max_size=5)
        self.assertEqual(queue.add(make_track("a")), 1)
        self.assertEqual(queue.add(make_track("b")), 2)

    def test_advance_plays_in_order_then_ends(self) -> None:
        queue = MusicQueue(max_size=5)
        first, second = make_track("a"), make_track("b")
        queue.add(first)
        queue.add(second)
        self.assertIs(queue.advance(), first)
        self.assertIs(queue.current, first)
        self.assertEqual(queue.upcoming, (second,))
        self.assertIs(queue.advance(), second)
        self.assertIsNone(queue.advance())
        self.assertIsNone(queue.current)

    def test_full_queue_rejects_new_tracks(self) -> None:
        queue = MusicQueue(max_size=1)
        queue.add(make_track("a"))
        with self.assertRaises(QueueFullError):
            queue.add(make_track("b"))

    def test_clear_removes_current_and_upcoming(self) -> None:
        queue = MusicQueue(max_size=5)
        queue.add(make_track("a"))
        queue.add(make_track("b"))
        queue.advance()
        queue.clear()
        self.assertIsNone(queue.current)
        self.assertEqual(queue.upcoming, ())


if __name__ == "__main__":
    unittest.main()
