"""Tests for the level curve and member ranking."""

import unittest

from leveling.curve import (
    BAR_EMPTY,
    BAR_FILLED,
    BAR_WIDTH,
    format_bar,
    level_for,
    progress_for,
    xp_for_next_level,
    xp_to_reach,
)
from leveling.ranking import find_member, rank_members


class CurveTests(unittest.TestCase):
    def test_xp_needed_grows_each_level(self) -> None:
        self.assertEqual(xp_for_next_level(0), 100)
        self.assertEqual(xp_for_next_level(1), 150)
        self.assertEqual(xp_for_next_level(10), 600)

    def test_cumulative_xp_matches_the_per_level_costs(self) -> None:
        self.assertEqual(xp_to_reach(0), 0)
        self.assertEqual(xp_to_reach(1), 100)
        self.assertEqual(xp_to_reach(2), 250)
        for level in range(30):
            self.assertEqual(xp_to_reach(level + 1) - xp_to_reach(level), xp_for_next_level(level))

    def test_level_changes_exactly_at_the_threshold(self) -> None:
        self.assertEqual(level_for(0), 0)
        self.assertEqual(level_for(99), 0)
        self.assertEqual(level_for(100), 1)
        self.assertEqual(level_for(249), 1)
        self.assertEqual(level_for(250), 2)

    def test_level_for_inverts_xp_to_reach(self) -> None:
        for level in range(50):
            self.assertEqual(level_for(xp_to_reach(level)), level)
            self.assertEqual(level_for(xp_to_reach(level + 1) - 1), level)

    def test_progress(self) -> None:
        progress = progress_for(175)
        self.assertEqual((progress.level, progress.xp_into_level, progress.xp_for_next), (1, 75, 150))
        self.assertEqual(progress.fraction, 0.5)

    def test_progress_at_zero(self) -> None:
        progress = progress_for(0)
        self.assertEqual((progress.level, progress.xp_into_level, progress.fraction), (0, 0, 0))

    def test_bar_fills_proportionally(self) -> None:
        self.assertEqual(format_bar(0), BAR_EMPTY * BAR_WIDTH)
        self.assertEqual(format_bar(0.5), BAR_FILLED * 5 + BAR_EMPTY * 5)
        self.assertEqual(format_bar(0.99), BAR_FILLED * 9 + BAR_EMPTY)
        self.assertEqual(len(format_bar(0.37)), BAR_WIDTH)


class RankingTests(unittest.TestCase):
    RANKING = [(30, 900), (10, 400), (20, 400), (40, 5)]

    def test_ranks_in_order_and_skips_members_who_left(self) -> None:
        names = {10: "Ann", 30: "Cy", 40: "Di"}
        ranked = rank_members(self.RANKING, names)
        self.assertEqual([(m.position, m.name) for m in ranked], [(1, "Cy"), (2, "Ann"), (3, "Di")])

    def test_members_know_their_level(self) -> None:
        (top,) = rank_members([(1, 260)], {1: "Ann"})
        self.assertEqual(top.level, 2)

    def test_no_one_ranked(self) -> None:
        self.assertEqual(rank_members([], {1: "Ann"}), [])
        self.assertEqual(rank_members(self.RANKING, {}), [])

    def test_find_member(self) -> None:
        ranked = rank_members(self.RANKING, {10: "Ann", 30: "Cy"})
        self.assertEqual(find_member(ranked, 10).position, 2)
        self.assertIsNone(find_member(ranked, 99))


if __name__ == "__main__":
    unittest.main()
