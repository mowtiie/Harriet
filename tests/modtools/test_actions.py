"""Tests for the moderation action pipeline."""

import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

import discord

from core.guild_settings import MODLOG_CHANNEL_KEY
from modtools.actions import (
    AUDIT_REASON_LIMIT,
    audit_reason,
    confirmation_text,
    enforce,
    format_dm,
)
from modtools.models import ModAction


class FakeUser:
    def __init__(self, user_id: int, name: str) -> None:
        self.id = user_id
        self.mention = f"<@{user_id}>"
        self.name = name
        self.sent: list[str] = []
        self.can_dm = True
        self.events: list[str] | None = None

    def __str__(self) -> str:
        return self.name

    async def send(self, text: str) -> None:
        if not self.can_dm:
            raise discord.Forbidden(mock.Mock(status=403), "closed")
        self.sent.append(text)
        if self.events is not None:
            self.events.append("dm")


def make_action(reason: str = "spam", duration: timedelta | None = None, guild=None) -> ModAction:
    guild = guild or SimpleNamespace(id=5, name="Test Server")
    return ModAction(
        "Ban", "banned", guild, FakeUser(1, "mod"), FakeUser(2, "target"), reason, duration
    )


class TextTests(unittest.TestCase):
    def test_audit_reason_names_the_moderator(self) -> None:
        self.assertEqual(audit_reason(make_action()), "mod (1): spam")

    def test_audit_reason_is_truncated(self) -> None:
        self.assertEqual(len(audit_reason(make_action("x" * 1000))), AUDIT_REASON_LIMIT)

    def test_dm_names_server_and_reason(self) -> None:
        self.assertEqual(
            format_dm(make_action()), "You were banned in **Test Server**.\nReason: spam"
        )

    def test_dm_includes_duration_when_present(self) -> None:
        text = format_dm(make_action(duration=timedelta(hours=2)))
        self.assertIn("banned for 2h in", text)

    def test_confirmation_reports_dm_outcome(self) -> None:
        action = make_action()
        self.assertEqual(confirmation_text(action, None), "Banned **target**.")
        self.assertIn("notified by DM", confirmation_text(action, True))
        self.assertIn("couldn't DM", confirmation_text(action, False))


class EnforceTests(unittest.IsolatedAsyncioTestCase):
    def make_bot(self, channel_id: str | None = None) -> mock.Mock:
        bot = mock.Mock()
        bot.guild_settings.get = mock.AsyncMock(return_value=channel_id)
        return bot

    async def test_dm_is_sent_before_the_action_runs(self) -> None:
        action = make_action()
        events: list[str] = []
        action.target.events = events

        async def perform() -> None:
            events.append("action")

        notified = await enforce(self.make_bot(), action, perform)
        self.assertTrue(notified)
        self.assertEqual(events, ["dm", "action"])

    async def test_closed_dms_do_not_block_the_action(self) -> None:
        action = make_action()
        action.target.can_dm = False
        perform = mock.AsyncMock()
        self.assertFalse(await enforce(self.make_bot(), action, perform))
        perform.assert_awaited_once()

    async def test_notify_false_skips_the_dm(self) -> None:
        action = make_action()
        self.assertIsNone(await enforce(self.make_bot(), action, mock.AsyncMock(), notify=False))
        self.assertEqual(action.target.sent, [])

    async def test_failed_action_propagates_and_skips_modlog(self) -> None:
        bot = self.make_bot("7")
        perform = mock.AsyncMock(side_effect=RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            await enforce(bot, make_action(), perform)
        bot.guild_settings.get.assert_not_awaited()

    async def test_posts_to_the_configured_modlog_channel(self) -> None:
        channel = mock.create_autospec(discord.TextChannel, instance=True)
        channel.send = mock.AsyncMock()
        guild = SimpleNamespace(id=5, name="Test Server", get_channel=lambda _id: channel)
        bot = self.make_bot("7")
        await enforce(bot, make_action(guild=guild), mock.AsyncMock())
        bot.guild_settings.get.assert_awaited_once_with(5, MODLOG_CHANNEL_KEY)
        channel.send.assert_awaited_once()

    async def test_no_modlog_channel_means_no_post(self) -> None:
        guild = mock.Mock(id=5)
        await enforce(self.make_bot(None), make_action(guild=guild), mock.AsyncMock())
        guild.get_channel.assert_not_called()


if __name__ == "__main__":
    unittest.main()
