"""Tests for role hierarchy rules and duration parsing."""

import unittest
from datetime import timedelta

from modtools.durations import parse_duration
from modtools.hierarchy import Standing, hierarchy_error

OWNER_ID = 1
BOT = Standing(member_id=99, top_role_position=10)


def error_for(actor: Standing, target: Standing) -> str | None:
    return hierarchy_error(actor, target, BOT, OWNER_ID)


class HierarchyErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.moderator = Standing(member_id=2, top_role_position=5)

    def test_lower_ranked_target_is_allowed(self) -> None:
        self.assertIsNone(error_for(self.moderator, Standing(3, 2)))

    def test_cannot_target_yourself(self) -> None:
        self.assertIn("yourself", error_for(self.moderator, self.moderator))

    def test_cannot_target_the_bot(self) -> None:
        self.assertIn("myself", error_for(self.moderator, BOT))

    def test_cannot_target_the_owner(self) -> None:
        self.assertIn("owner", error_for(self.moderator, Standing(OWNER_ID, 1)))

    def test_equal_or_higher_role_than_actor_is_refused(self) -> None:
        self.assertIn("yours", error_for(self.moderator, Standing(3, 5)))
        self.assertIn("yours", error_for(self.moderator, Standing(3, 6)))

    def test_role_at_or_above_the_bot_is_refused(self) -> None:
        owner = Standing(OWNER_ID, 20)
        self.assertIn("mine", error_for(owner, Standing(3, 10)))

    def test_owner_may_target_roles_above_themselves(self) -> None:
        owner = Standing(OWNER_ID, 1)
        self.assertIsNone(error_for(owner, Standing(3, 9)))


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self) -> None:
        self.assertEqual(parse_duration("30s"), timedelta(seconds=30))
        self.assertEqual(parse_duration("10m"), timedelta(minutes=10))
        self.assertEqual(parse_duration("2h"), timedelta(hours=2))
        self.assertEqual(parse_duration("3d"), timedelta(days=3))
        self.assertEqual(parse_duration("1w"), timedelta(weeks=1))

    def test_combined_units_ignoring_case_and_spaces(self) -> None:
        self.assertEqual(parse_duration("1H 30m"), timedelta(hours=1, minutes=30))

    def test_rejects_unreadable_text(self) -> None:
        for text in ("", "soon", "10", "5x", "1h later", "-5m"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)

    def test_rejects_zero(self) -> None:
        with self.assertRaises(ValueError):
            parse_duration("0m")

    def test_rejects_more_than_the_maximum(self) -> None:
        self.assertEqual(parse_duration("28d"), timedelta(days=28))
        with self.assertRaises(ValueError):
            parse_duration("29d")


if __name__ == "__main__":
    unittest.main()
