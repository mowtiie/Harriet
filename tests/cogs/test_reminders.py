"""Tests for reminder delivery and the new views' payloads."""

import unittest
from datetime import datetime, timezone
from unittest import mock

import discord

from cogs.reminders import Reminders
from features.reminders.reminders_view import build_reminders_view
from features.reminders.store import Reminder
from views.profile_view import build_avatar_view, build_profile_view

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


class ViewPayloadTests(unittest.TestCase):
    def test_profile_view_with_and_without_thumbnail(self) -> None:
        fields = [("ID", "`1`")]
        with_icon = build_profile_view("Name", "Sub", fields, "https://example.com/a.png")
        without_icon = build_profile_view("Name", "Sub", fields)
        self.assertEqual(with_icon.to_components()[0]["components"][0]["type"], 9)
        self.assertEqual(without_icon.to_components()[0]["components"][0]["type"], 10)

    def test_avatar_view_has_one_gallery_item_per_avatar(self) -> None:
        urls = [
            ("Server avatar", "https://example.com/s.png"),
            ("Global avatar", "https://example.com/g.png"),
        ]
        container = build_avatar_view("Name", urls).to_components()[0]
        gallery = container["components"][1]
        self.assertEqual(len(gallery["items"]), 2)

    def test_reminders_view_builds(self) -> None:
        self.assertTrue(build_reminders_view([REMINDER]).to_components())


if __name__ == "__main__":
    unittest.main()
