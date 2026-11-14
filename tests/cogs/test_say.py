"""Tests for the /say command flow."""

import unittest
from unittest import mock

import discord
from discord.ext import commands

from cogs.moderation import Moderation
from core.errors import UserError
from features.modtools.say import MAX_MESSAGE_LENGTH, SAY_COOLDOWN_SECONDS

ALLOWED = discord.Permissions(view_channel=True, send_messages=True)
CAN_PING = discord.Permissions(view_channel=True, send_messages=True, mention_everyone=True)
SILENCED = discord.Permissions(view_channel=True, send_messages=False)
AUTHOR = mock.Mock(id=1)
BOT = mock.Mock(id=2)


def make_channel(member_permissions: discord.Permissions = ALLOWED, name: str = "general"):
    channel = mock.Mock(spec=discord.TextChannel)
    channel.mention = f"<#{name}>"
    channel.send = mock.AsyncMock(
        return_value=mock.Mock(content="sent", jump_url="https://discord.com/channels/1/2/3")
    )
    permissions = {AUTHOR: member_permissions, BOT: ALLOWED}
    channel.permissions_for.side_effect = permissions.__getitem__
    return channel


def make_ctx(channel, slash: bool = True) -> mock.Mock:
    ctx = mock.Mock()
    ctx.interaction = mock.Mock() if slash else None
    ctx.author = AUTHOR
    ctx.guild.me = BOT
    ctx.channel = channel
    ctx.defer = mock.AsyncMock()
    ctx.send = mock.AsyncMock()
    ctx.message.delete = mock.AsyncMock()
    return ctx


def make_cog() -> Moderation:
    return Moderation(mock.Mock())


class SayCommandTests(unittest.IsolatedAsyncioTestCase):
    async def run_say(self, ctx, message: str = "Hello, everyone!", channel=None) -> mock.AsyncMock:
        with (
            mock.patch("cogs.moderation.post_to_modlog", new=mock.AsyncMock()) as modlog,
            mock.patch("cogs.moderation.build_say_log_view", return_value="log-view"),
        ):
            await Moderation.say.callback(make_cog(), ctx, channel, message=message)
        return modlog

    async def test_it_posts_the_message_in_the_current_channel(self) -> None:
        here = make_channel()
        await self.run_say(make_ctx(here))
        here.send.assert_awaited_once()
        self.assertEqual(here.send.await_args.args, ("Hello, everyone!",))

    async def test_it_can_post_in_another_channel(self) -> None:
        here, there = make_channel(name="here"), make_channel(name="there")
        await self.run_say(make_ctx(here), channel=there)
        there.send.assert_awaited_once()
        here.send.assert_not_awaited()

    async def test_a_slash_command_confirms_privately(self) -> None:
        here = make_channel()
        ctx = make_ctx(here)
        await self.run_say(ctx)
        ctx.defer.assert_awaited_once_with(ephemeral=True)
        ctx.send.assert_awaited_once_with("Sent in <#general>.", ephemeral=True)
        ctx.message.delete.assert_not_awaited()

    async def test_a_prefix_command_removes_the_message_that_asked_for_it(self) -> None:
        ctx = make_ctx(make_channel(), slash=False)
        await self.run_say(ctx)
        ctx.message.delete.assert_awaited_once()
        ctx.send.assert_not_awaited()
        ctx.defer.assert_not_awaited()

    async def test_failing_to_remove_the_prefix_message_does_not_matter(self) -> None:
        here = make_channel()
        ctx = make_ctx(here, slash=False)
        ctx.message.delete.side_effect = discord.Forbidden(mock.Mock(status=403), "no")
        await self.run_say(ctx)
        here.send.assert_awaited_once()

    async def test_without_the_ping_permission_mass_mentions_stay_silent(self) -> None:
        here = make_channel(ALLOWED)
        await self.run_say(make_ctx(here), "@everyone hello")
        rules = here.send.await_args.kwargs["allowed_mentions"]
        self.assertFalse(rules.everyone)
        self.assertFalse(rules.roles)

    async def test_with_the_ping_permission_they_work(self) -> None:
        here = make_channel(CAN_PING)
        await self.run_say(make_ctx(here), "@everyone hello")
        self.assertTrue(here.send.await_args.kwargs["allowed_mentions"].everyone)

    async def test_the_ping_permission_is_checked_in_the_target_channel(self) -> None:
        here, there = make_channel(ALLOWED, "here"), make_channel(CAN_PING, "there")
        await self.run_say(make_ctx(here), channel=there)
        self.assertTrue(there.send.await_args.kwargs["allowed_mentions"].everyone)

    async def test_it_is_written_to_the_mod_log(self) -> None:
        here = make_channel()
        modlog = await self.run_say(make_ctx(here))
        modlog.assert_awaited_once()
        self.assertEqual(modlog.await_args.args[2], "log-view")

    async def test_a_channel_the_member_cannot_post_in_is_refused_and_nothing_is_sent(self) -> None:
        locked = make_channel(SILENCED)
        with self.assertRaises(UserError):
            await self.run_say(make_ctx(make_channel()), channel=locked)
        locked.send.assert_not_awaited()

    async def test_an_empty_or_too_long_message_is_refused_and_nothing_is_sent(self) -> None:
        for message in ("   ", "x" * (MAX_MESSAGE_LENGTH + 1)):
            here = make_channel()
            with self.subTest(length=len(message)), self.assertRaises(commands.BadArgument):
                await self.run_say(make_ctx(here), message)
            here.send.assert_not_awaited()


class SayPermissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_it_needs_manage_messages(self) -> None:
        ctx = mock.Mock()
        ctx.permissions = discord.Permissions(send_messages=True)
        failures = []
        for check in Moderation.say.checks:
            try:
                await discord.utils.maybe_coroutine(check, ctx)
            except commands.CheckFailure as error:
                failures.append(error)
        self.assertTrue(any(isinstance(f, commands.MissingPermissions) for f in failures))
        self.assertIn("manage_messages", failures[0].missing_permissions)

    async def test_it_lets_someone_with_manage_messages_through(self) -> None:
        ctx = mock.Mock()
        ctx.permissions = discord.Permissions(manage_messages=True)
        for check in Moderation.say.checks:
            self.assertTrue(await discord.utils.maybe_coroutine(check, ctx))

    def test_it_has_a_short_cooldown_per_person(self) -> None:
        cooldown = Moderation.say._buckets._cooldown
        self.assertEqual((cooldown.rate, cooldown.per), (1, SAY_COOLDOWN_SECONDS))
        self.assertEqual(Moderation.say._buckets._type, commands.BucketType.user)


if __name__ == "__main__":
    unittest.main()
