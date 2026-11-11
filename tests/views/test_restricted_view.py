"""Tests for the shared view that only certain users can press."""

import unittest
from types import SimpleNamespace
from unittest import mock

import discord

from views.restricted_view import RestrictedView

ALLOWED, STRANGER = 1, 2


class CountingView(RestrictedView):
    def __init__(self, allowed_user_ids: tuple[int, ...] = (ALLOWED,)) -> None:
        super().__init__(allowed_user_ids, timeout_seconds=60)
        self.renders = 0

    def _render(self) -> None:
        self.renders += 1


def make_interaction(user_id: int) -> mock.Mock:
    interaction = mock.Mock()
    interaction.user = SimpleNamespace(id=user_id)
    interaction.response.send_message = mock.AsyncMock()
    return interaction


class RestrictedViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_allowed_users_pass(self) -> None:
        interaction = make_interaction(ALLOWED)
        self.assertTrue(await CountingView().interaction_check(interaction))
        interaction.response.send_message.assert_not_awaited()

    async def test_strangers_are_turned_away_privately(self) -> None:
        interaction = make_interaction(STRANGER)
        self.assertFalse(await CountingView().interaction_check(interaction))
        self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])

    async def test_several_allowed_users(self) -> None:
        view = CountingView((ALLOWED, STRANGER))
        self.assertTrue(await view.interaction_check(make_interaction(STRANGER)))

    async def test_timeout_rerenders_and_edits_the_message(self) -> None:
        view = CountingView()
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        self.assertEqual(view.renders, 1)
        view.message.edit.assert_awaited_once_with(view=view)

    async def test_timeout_without_a_message_still_rerenders(self) -> None:
        view = CountingView()
        await view.on_timeout()
        self.assertEqual(view.renders, 1)

    async def test_failed_edit_on_timeout_is_not_fatal(self) -> None:
        view = CountingView()
        error = discord.NotFound(mock.Mock(status=404), "gone")
        view.message = mock.Mock(edit=mock.AsyncMock(side_effect=error))
        await view.on_timeout()


if __name__ == "__main__":
    unittest.main()
