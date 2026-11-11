"""Tests for which commands the help menu shows."""

import unittest
from types import SimpleNamespace
from unittest import mock

from discord.ext import commands

from cogs.help import is_visible_to
from core.errors import UserError


def make_command(hidden: bool = False, **can_run: object) -> SimpleNamespace:
    return SimpleNamespace(hidden=hidden, can_run=mock.AsyncMock(**can_run))


class IsVisibleToTests(unittest.IsolatedAsyncioTestCase):
    async def test_command_the_user_can_run_is_visible(self) -> None:
        self.assertTrue(await is_visible_to(make_command(return_value=True), mock.Mock()))

    async def test_hidden_commands_are_never_shown(self) -> None:
        command = make_command(hidden=True, return_value=True)
        self.assertFalse(await is_visible_to(command, mock.Mock()))
        command.can_run.assert_not_awaited()

    async def test_missing_permissions_hide_the_command(self) -> None:
        error = commands.MissingPermissions(["ban_members"])
        self.assertFalse(await is_visible_to(make_command(side_effect=error), mock.Mock()))

    async def test_owner_only_commands_are_hidden_from_others(self) -> None:
        self.assertFalse(
            await is_visible_to(make_command(side_effect=commands.NotOwner()), mock.Mock())
        )

    async def test_a_check_that_explains_itself_keeps_the_command_visible(self) -> None:
        error = UserError("Join a voice channel first.")
        self.assertTrue(await is_visible_to(make_command(side_effect=error), mock.Mock()))


if __name__ == "__main__":
    unittest.main()
