"""Tests for reminder delivery."""

import unittest
from datetime import datetime, timezone
from unittest import mock

import discord

from cogs.reminders import Reminders
from features.reminders.store import Reminder

DUE = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
REMINDER = Reminder(id=4, user_id=9, channel_id=1, text="stand up", due_at=DUE)


def make_cog(channel: object | None, user: object | None = None) -> Reminders:
    bot = mock.Mock()
    bot.get_channel.return_value = channel
    bot.fetch_user = mock.AsyncMock(return_value=user)
    return Reminders(bot)


def forbidden() -> discord.Forbidden:
    return discord.Forbidden(mock.Mock(status=403), "no access")


class DeliverTests(unittest.IsolatedAsyncioTestCase):
    async def test_posts_in_the_original_channel_pinging_only_the_user(self) -> None:
        channel = mock.Mock(send=mock.AsyncMock())
        await make_cog(channel)._deliver(REMINDER)
        channel.send.assert_awaited_once()
        mentions = channel.send.await_args.kwargs["allowed_mentions"]
        self.assertFalse(mentions.everyone)
        self.assertFalse(mentions.roles)
        self.assertEqual([user.id for user in mentions.users], [9])

    async def test_falls_back_to_dm_when_the_channel_is_missing(self) -> None:
        user = mock.Mock(send=mock.AsyncMock())
        await make_cog(None, user)._deliver(REMINDER)
        user.send.assert_awaited_once()

    async def test_falls_back_to_dm_when_the_channel_rejects_the_message(self) -> None:
        channel = mock.Mock(send=mock.AsyncMock(side_effect=forbidden()))
        user = mock.Mock(send=mock.AsyncMock())
        await make_cog(channel, user)._deliver(REMINDER)
        user.send.assert_awaited_once()

    async def test_gives_up_quietly_when_nothing_works(self) -> None:
        user = mock.Mock(send=mock.AsyncMock(side_effect=forbidden()))
        await make_cog(None, user)._deliver(REMINDER)
        user.send.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
