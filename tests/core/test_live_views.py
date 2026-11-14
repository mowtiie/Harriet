"""Tests for counting views that are still running."""

import gc
import unittest

from core.live_views import count_unfinished, track
from features.games.game_view import GameView


class FakeView:
    def __init__(self) -> None:
        self.finished = False

    def is_finished(self) -> bool:
        return self.finished


class CountUnfinishedTests(unittest.TestCase):
    def test_finished_views_are_not_counted(self) -> None:
        before = count_unfinished()
        running, done = FakeView(), FakeView()
        done.finished = True
        track(running)
        track(done)
        self.assertEqual(count_unfinished(), before + 1)
        running.finished = True
        self.assertEqual(count_unfinished(), before)

    def test_a_view_nobody_holds_any_more_disappears_from_the_count(self) -> None:
        before = count_unfinished()
        track(FakeView())
        gc.collect()
        self.assertEqual(count_unfinished(), before)


class GameViewTrackingTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_game_counts_until_it_stops(self) -> None:
        before = count_unfinished()
        first, second = GameView((1,), 60, None), GameView((1,), 60, None)
        self.assertEqual(count_unfinished(), before + 2)
        first.stop()
        self.assertEqual(count_unfinished(), before + 1)
        second.stop()
        self.assertEqual(count_unfinished(), before)


if __name__ == "__main__":
    unittest.main()
