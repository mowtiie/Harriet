"""Tests for which commands the help menu shows."""

import unittest
from types import SimpleNamespace
from unittest import mock

import discord
from discord.ext import commands

from cogs.help import Help, is_visible_to
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


def make_help_cog(*fetches: list[str] | Exception) -> Help:
    """A Help cog whose Discord lookups return the given lists of command names in turn."""
    bot = mock.Mock()
    responses = [
        fetch
        if isinstance(fetch, Exception)
        else [SimpleNamespace(name=name, mention=f"</{name}:1>") for name in fetch]
        for fetch in fetches
    ]
    bot.tree.fetch_commands = mock.AsyncMock(side_effect=responses)
    return Help(bot)


class LoadSlashMentionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_links_are_fetched_once_while_every_command_is_known(self) -> None:
        cog = make_help_cog(["rps", "guess"])
        first = await cog._load_slash_mentions({"rps"})
        second = await cog._load_slash_mentions({"rps", "guess"})
        self.assertEqual(first, {"rps": "</rps:1>", "guess": "</guess:1>"})
        self.assertIs(second, first)
        cog.bot.tree.fetch_commands.assert_awaited_once()

    async def test_a_command_added_later_triggers_a_fresh_fetch(self) -> None:
        cog = make_help_cog(["rps"], ["rps", "minesweeper"])
        await cog._load_slash_mentions({"rps"})
        refreshed = await cog._load_slash_mentions({"rps", "minesweeper"})
        self.assertIn("minesweeper", refreshed)
        self.assertEqual(cog.bot.tree.fetch_commands.await_count, 2)

    async def test_a_failed_refresh_keeps_the_links_we_already_have(self) -> None:
        failure = discord.HTTPException(mock.Mock(status=500, reason="x"), "boom")
        cog = make_help_cog(["rps"], failure)
        await cog._load_slash_mentions({"rps"})
        self.assertEqual(await cog._load_slash_mentions({"rps", "new"}), {"rps": "</rps:1>"})

    async def test_a_failed_first_fetch_gives_no_links(self) -> None:
        failure = discord.HTTPException(mock.Mock(status=500, reason="x"), "boom")
        self.assertEqual(await make_help_cog(failure)._load_slash_mentions({"rps"}), {})


if __name__ == "__main__":
    unittest.main()
