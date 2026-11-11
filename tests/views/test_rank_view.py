"""Tests for rank card and leaderboard views."""

import unittest
from types import SimpleNamespace
from unittest import mock

from leveling.ranking import RankedMember
from views.rank_view import (
    EMPTY_BOARD_TEXT,
    PAGE_SIZE,
    LeaderboardView,
    format_leaderboard_page,
    page_count,
    rank_fields,
)

AUTHOR, OTHER = 1, 2


def make_members(count: int) -> list[RankedMember]:
    return [RankedMember(i, 100 + i, f"user{i}", 1000 - i) for i in range(1, count + 1)]


def make_interaction(user_id: int) -> mock.Mock:
    interaction = mock.Mock()
    interaction.user = SimpleNamespace(id=user_id)
    interaction.response.send_message = mock.AsyncMock()
    interaction.response.edit_message = mock.AsyncMock()
    return interaction


class RankFieldsTests(unittest.TestCase):
    def test_fields_for_a_member_partway_through_a_level(self) -> None:
        fields = dict(rank_fields(1175))
        self.assertEqual(fields["Level"], "5")
        self.assertEqual(fields["Total XP"], "1,175")
        self.assertEqual(fields["Next level"], "175 / 350 XP")

    def test_fields_for_a_member_with_no_xp(self) -> None:
        fields = dict(rank_fields(0))
        self.assertEqual(fields["Level"], "0")
        self.assertEqual(fields["Next level"], "0 / 100 XP")


class FormatLeaderboardTests(unittest.TestCase):
    def test_empty_board(self) -> None:
        self.assertEqual(format_leaderboard_page([], 0), EMPTY_BOARD_TEXT)

    def test_line_shows_position_name_level_and_xp(self) -> None:
        line = format_leaderboard_page([RankedMember(1, 5, "Ann", 1234)], 0)
        self.assertEqual(line, "`1.` **Ann** · Level 5 · 1,234 XP")

    def test_pages_hold_page_size_members(self) -> None:
        members = make_members(PAGE_SIZE + 3)
        self.assertEqual(len(format_leaderboard_page(members, 0).splitlines()), PAGE_SIZE)
        second = format_leaderboard_page(members, 1).splitlines()
        self.assertEqual(len(second), 3)
        self.assertTrue(second[0].startswith(f"`{PAGE_SIZE + 1}.`"))

    def test_page_count(self) -> None:
        self.assertEqual(page_count(0), 1)
        self.assertEqual(page_count(PAGE_SIZE), 1)
        self.assertEqual(page_count(PAGE_SIZE + 1), 2)


class LeaderboardViewTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self, count: int) -> LeaderboardView:
        return LeaderboardView(make_members(count), AUTHOR, timeout_seconds=60)

    async def test_only_the_author_can_use_the_buttons(self) -> None:
        view = self.make_view(25)
        self.assertTrue(await view.interaction_check(make_interaction(AUTHOR)))
        stranger = make_interaction(OTHER)
        self.assertFalse(await view.interaction_check(stranger))
        stranger.response.send_message.assert_awaited_once()

    async def test_paging_moves_within_bounds(self) -> None:
        view = self.make_view(25)
        interaction = make_interaction(AUTHOR)
        await view._turn_page(-1, interaction)
        self.assertEqual(view._page, 0)
        await view._turn_page(1, interaction)
        await view._turn_page(1, interaction)
        await view._turn_page(1, interaction)
        self.assertEqual(view._page, 2)
        self.assertEqual(interaction.response.edit_message.await_count, 4)

    async def test_single_page_board_has_no_buttons(self) -> None:
        view = self.make_view(3)
        self.assertFalse([item for item in view.walk_children() if hasattr(item, "label")])

    async def test_timeout_disables_the_buttons(self) -> None:
        view = self.make_view(25)
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        view.message.edit.assert_awaited_once()
        buttons = [item for item in view.walk_children() if hasattr(item, "label")]
        self.assertEqual(len(buttons), 2)
        self.assertTrue(all(button.disabled for button in buttons))


if __name__ == "__main__":
    unittest.main()
