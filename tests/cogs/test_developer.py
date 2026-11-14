"""Tests for the owner-only developer commands."""

import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import discord
from discord.ext import commands

import config
from cogs.developer import DM_BLOCKED_TEXT, Developer, deliver_privately
from core.errors import UserError
from features.devtools.backup import BackupError

OWNER_ONLY = ("reload", "status", "logs", "backup")
LOG = "\n".join(
    [
        "[2026-11-14 17:07:05] [INFO    ] bot: Loaded cog: cogs.games",
        "[2026-11-14 17:08:10] [ERROR   ] bot: Failed to load cog: cogs.broken",
        "Traceback (most recent call last):",
        "SyntaxError: invalid syntax",
    ]
)


def make_ctx(slash: bool) -> mock.Mock:
    ctx = mock.Mock()
    ctx.interaction = mock.Mock() if slash else None
    ctx.defer = mock.AsyncMock()
    ctx.send = mock.AsyncMock()
    ctx.author.send = mock.AsyncMock()
    return ctx


def make_cog() -> Developer:
    bot = SimpleNamespace(
        started_at=discord.utils.utcnow() - timedelta(hours=1, minutes=30),
        started_commit="abc1234",
        latency=0.048,
        guilds=[object(), object()],
        voice_clients=[object()],
        extensions={"cogs.games": object(), "cogs.fun": object()},
        tree=mock.Mock(get_commands=mock.Mock(return_value=[object()] * 3)),
    )
    return Developer(bot)


class OwnerOnlyTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_developer_command_refuses_other_people(self) -> None:
        ctx = mock.Mock()
        ctx.bot.is_owner = mock.AsyncMock(return_value=False)
        for name in OWNER_ONLY:
            with self.subTest(command=name):
                predicate = getattr(Developer, name).checks[0]
                with self.assertRaises(commands.NotOwner):
                    await predicate(ctx)

    async def test_the_owner_is_let_through(self) -> None:
        ctx = mock.Mock()
        ctx.bot.is_owner = mock.AsyncMock(return_value=True)
        for name in OWNER_ONLY:
            self.assertTrue(await getattr(Developer, name).checks[0](ctx))


class DeliverPrivatelyTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_slash_command_gets_a_private_reply(self) -> None:
        ctx = make_ctx(slash=True)
        await deliver_privately(ctx, "secret")
        ctx.send.assert_awaited_once_with("secret", file=None, ephemeral=True)
        ctx.author.send.assert_not_awaited()

    async def test_a_prefix_command_goes_to_dms_not_the_channel(self) -> None:
        ctx = make_ctx(slash=False)
        await deliver_privately(ctx, "secret")
        ctx.author.send.assert_awaited_once_with("secret", file=None)
        ctx.send.assert_awaited_once_with("Sent you a DM.")

    async def test_closed_dms_are_explained_and_nothing_leaks_to_the_channel(self) -> None:
        ctx = make_ctx(slash=False)
        ctx.author.send.side_effect = discord.Forbidden(mock.Mock(status=403, reason="x"), "no")
        with self.assertRaises(UserError) as caught:
            await deliver_privately(ctx, "secret")
        self.assertEqual(str(caught.exception), DM_BLOCKED_TEXT)
        ctx.send.assert_not_awaited()


class StatusTests(unittest.IsolatedAsyncioTestCase):
    async def test_status_gathers_everything_into_one_report(self) -> None:
        cog = make_cog()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "harriet.db"
            database.write_bytes(b"x" * 2048)
            with (
                mock.patch.object(config, "DATABASE_PATH", database),
                mock.patch("cogs.developer.read_log_tail", return_value=LOG),
                mock.patch("cogs.developer.current_commit", return_value="def5678"),
                mock.patch("cogs.developer.has_uncommitted_changes", return_value=True),
                mock.patch("cogs.developer.count_unfinished", return_value=4),
                mock.patch(
                    "cogs.developer.discover_extensions",
                    return_value=["cogs.games", "cogs.fun", "cogs.new"],
                ),
            ):
                info = await cog._collect_status()
        self.assertEqual(info.uptime.total_seconds() // 60, 90)
        self.assertEqual(info.latency_ms, 48)
        self.assertEqual((info.guild_count, info.voice_connections, info.active_games), (2, 1, 4))
        self.assertEqual((info.commit, info.started_commit), ("def5678", "abc1234"))
        self.assertTrue(info.has_uncommitted_changes)
        self.assertEqual((info.loaded_cogs, info.unloaded_cogs), (2, ("cogs.new",)))
        self.assertEqual(info.command_count, 3)
        self.assertEqual(info.database_bytes, 2048)
        self.assertEqual(info.error_count, 1)
        self.assertEqual(info.last_error, "17:08:10 bot: Failed to load cog: cogs.broken")

    async def test_a_missing_database_and_clean_log_are_handled(self) -> None:
        cog = make_cog()
        with (
            mock.patch.object(config, "DATABASE_PATH", Path("no-such-folder") / "x.db"),
            mock.patch("cogs.developer.read_log_tail", return_value=""),
            mock.patch("cogs.developer.current_commit", return_value=None),
            mock.patch("cogs.developer.has_uncommitted_changes", return_value=None),
        ):
            info = await cog._collect_status()
        self.assertIsNone(info.database_bytes)
        self.assertEqual((info.error_count, info.last_error), (0, None))
        self.assertIsNone(info.commit)

    async def test_the_status_command_replies_privately(self) -> None:
        cog, ctx = make_cog(), make_ctx(slash=True)
        with (
            mock.patch("cogs.developer.read_log_tail", return_value=""),
            mock.patch("cogs.developer.current_commit", return_value="abc1234"),
            mock.patch("cogs.developer.has_uncommitted_changes", return_value=False),
        ):
            await Developer.status.callback(cog, ctx)
        ctx.defer.assert_awaited_once_with(ephemeral=True)
        text = ctx.send.await_args.args[0]
        self.assertTrue(text.startswith("**Status**"))
        self.assertTrue(ctx.send.await_args.kwargs["ephemeral"])


class LogsCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_short_log_is_sent_inline(self) -> None:
        cog, ctx = make_cog(), make_ctx(slash=True)
        with mock.patch("cogs.developer.read_log_tail", return_value=LOG):
            await Developer.logs.callback(cog, ctx, 10, "errors")
        message = ctx.send.await_args.args[0]
        self.assertIn("SyntaxError", message)
        self.assertNotIn("Loaded cog", message)
        self.assertIsNone(ctx.send.await_args.kwargs["file"])

    async def test_a_long_log_is_attached_as_a_file(self) -> None:
        cog, ctx = make_cog(), make_ctx(slash=True)
        record = "[2026-11-14 17:07:05] [INFO    ] bot: line {} " + "x" * 60
        big = "\n".join(record.format(n) for n in range(60))
        with mock.patch("cogs.developer.read_log_tail", return_value=big):
            await Developer.logs.callback(cog, ctx, 60, "all")
        attachment = ctx.send.await_args.kwargs["file"]
        self.assertEqual(attachment.filename, "bot-log.txt")


class BackupCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_the_snapshot_is_sent_as_a_private_file(self) -> None:
        cog, ctx = make_cog(), make_ctx(slash=True)
        with mock.patch("cogs.developer.snapshot_database", return_value=b"sqlite-bytes"):
            await Developer.backup.callback(cog, ctx)
        kwargs = ctx.send.await_args.kwargs
        self.assertTrue(kwargs["ephemeral"])
        self.assertRegex(kwargs["file"].filename, r"^harriet-\d{8}-\d{6}\.db$")
        self.assertIn("user IDs", ctx.send.await_args.args[0])

    async def test_a_backup_problem_is_shown_to_the_owner(self) -> None:
        cog, ctx = make_cog(), make_ctx(slash=True)
        with mock.patch("cogs.developer.snapshot_database", side_effect=BackupError("too big")):
            with self.assertRaises(UserError) as caught:
                await Developer.backup.callback(cog, ctx)
        self.assertEqual(str(caught.exception), "too big")
        ctx.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
