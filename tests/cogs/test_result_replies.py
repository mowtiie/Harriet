"""Tests that the result commands answer with cards and keep user text from pinging."""

import random
import unittest
from datetime import timedelta
from unittest import mock

from discord import ui
from discord.ext import commands

from cogs.fun import MAX_QUESTION_LENGTH, Fun
from cogs.reminders import Reminders
from cogs.tools import Tools
from core.errors import UserError


def texts_in(view: ui.LayoutView) -> list[str]:
    return [item.content for item in view.walk_children() if isinstance(item, ui.TextDisplay)]


def make_ctx() -> mock.Mock:
    ctx = mock.Mock()
    ctx.author.display_name = "Alice"
    ctx.author.id = 7
    ctx.channel.id = 3
    ctx.send = mock.AsyncMock()
    return ctx


def sent_card(ctx: mock.Mock) -> ui.LayoutView:
    return ctx.send.await_args.kwargs["view"]


class FunCardTests(unittest.IsolatedAsyncioTestCase):
    def make_cog(self) -> Fun:
        cog = Fun(mock.Mock())
        cog._rng = random.Random(1)
        return cog

    async def test_eightball_answers_with_a_card_and_cannot_ping(self) -> None:
        ctx = make_ctx()
        await Fun.eightball.callback(self.make_cog(), ctx, question="Will  it   rain @everyone?")
        texts = texts_in(sent_card(ctx))
        self.assertEqual(texts[1], "> Will it rain @everyone?")
        self.assertEqual(texts[-1], "-# Asked by Alice")
        rules = ctx.send.await_args.kwargs["allowed_mentions"]
        self.assertFalse(rules.everyone)

    async def test_a_very_long_question_is_still_refused(self) -> None:
        ctx = make_ctx()
        too_long = "x" * (MAX_QUESTION_LENGTH + 1)
        with self.assertRaises(UserError):
            await Fun.eightball.callback(self.make_cog(), ctx, question=too_long)
        ctx.send.assert_not_awaited()

    async def test_coinflip_answers_with_a_card(self) -> None:
        ctx = make_ctx()
        await Fun.coinflip.callback(self.make_cog(), ctx)
        title, answer = texts_in(sent_card(ctx))
        self.assertEqual(title, "### 🪙 Coin flip")
        self.assertIn(answer, ("## Heads", "## Tails"))


class ToolsCardTests(unittest.IsolatedAsyncioTestCase):
    def make_cog(self) -> Tools:
        cog = Tools()
        cog._rng = random.Random(1)
        return cog

    async def test_roll_shows_the_total_and_the_dice_it_was_made_from(self) -> None:
        ctx = make_ctx()
        await Tools.roll.callback(self.make_cog(), ctx, dice="2d6+3")
        texts = texts_in(sent_card(ctx))
        self.assertEqual(texts[0], "### 🎲 Dice roll")
        self.assertTrue(texts[1].startswith("## "))
        self.assertTrue(texts[2].startswith("-# 2d6+3 · "))

    async def test_a_bad_roll_is_a_bad_argument_and_sends_nothing(self) -> None:
        ctx = make_ctx()
        with self.assertRaises(commands.BadArgument):
            await Tools.roll.callback(self.make_cog(), ctx, dice="banana")
        ctx.send.assert_not_awaited()

    async def test_choose_shows_the_options_and_cannot_ping(self) -> None:
        ctx = make_ctx()
        await Tools.choose.callback(self.make_cog(), ctx, options="pizza, sushi, @everyone")
        texts = texts_in(sent_card(ctx))
        self.assertEqual(texts[1], "> pizza · sushi · @everyone")
        self.assertIn(texts[2], ("## pizza", "## sushi", "## @everyone"))
        self.assertFalse(ctx.send.await_args.kwargs["allowed_mentions"].everyone)

    async def test_time_answers_with_a_card_in_the_zone_that_was_asked_for(self) -> None:
        ctx = make_ctx()
        await Tools.time.callback(self.make_cog(), ctx, when="2030-01-02 09:30 UTC+2")
        texts = texts_in(sent_card(ctx))
        self.assertEqual(texts[0], "### 🕒 Time")
        self.assertTrue(texts[1].startswith("## <t:"))
        self.assertIn("Read as Wed 02 Jan 2030, 09:30 in UTC+02:00 (UTC+02:00)", texts[2])

    async def test_an_unreadable_time_is_a_bad_argument(self) -> None:
        ctx = make_ctx()
        with self.assertRaises(commands.BadArgument):
            await Tools.time.callback(self.make_cog(), ctx, when="whenever")
        ctx.send.assert_not_awaited()


class ReminderCardTests(unittest.IsolatedAsyncioTestCase):
    def make_cog(self, cancelled: bool = True) -> Reminders:
        bot = mock.Mock()
        bot.reminder_store.count_for = mock.AsyncMock(return_value=0)
        bot.reminder_store.add = mock.AsyncMock(return_value=12)
        bot.reminder_store.cancel = mock.AsyncMock(return_value=cancelled)
        return Reminders(bot)

    async def test_setting_a_reminder_confirms_privately_with_a_card(self) -> None:
        ctx = make_ctx()
        await Reminders.remind.callback(self.make_cog(), ctx, "2h", text="stand up")
        self.assertTrue(ctx.send.await_args.kwargs["ephemeral"])
        texts = texts_in(sent_card(ctx))
        self.assertEqual(texts[0], "### ⏰ Reminder set")
        self.assertIn("`#12`", texts[-1])

    async def test_cancelling_confirms_privately_with_a_card(self) -> None:
        ctx = make_ctx()
        await Reminders.unremind.callback(self.make_cog(), ctx, 12)
        self.assertTrue(ctx.send.await_args.kwargs["ephemeral"])
        self.assertEqual(texts_in(sent_card(ctx))[0], "### ⏰ Reminder cancelled")

    async def test_cancelling_a_reminder_that_does_not_exist_is_still_an_error(self) -> None:
        ctx = make_ctx()
        with self.assertRaises(UserError):
            await Reminders.unremind.callback(self.make_cog(cancelled=False), ctx, 99)
        ctx.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
