"""Tests for rewarding game wins."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import discord

import config
from features.leveling.awards import XpGain, amount_for_win, format_gain_note, reward_win
from features.leveling.store import ExperienceStore


class XpGainTests(unittest.TestCase):
    def test_level_up_is_detected_when_a_threshold_is_crossed(self) -> None:
        gain = XpGain(amount=50, total=120)
        self.assertEqual((gain.previous_level, gain.new_level), (0, 1))
        self.assertTrue(gain.leveled_up)

    def test_no_level_up_inside_a_level(self) -> None:
        self.assertFalse(XpGain(amount=10, total=60).leveled_up)

    def test_landing_exactly_on_a_threshold_levels_up(self) -> None:
        self.assertTrue(XpGain(amount=50, total=100).leveled_up)

    def test_note_mentions_the_level_only_on_level_up(self) -> None:
        self.assertEqual(format_gain_note(XpGain(10, 60)), "+10 XP")
        self.assertEqual(format_gain_note(XpGain(50, 120)), "+50 XP · Level 1")


class AmountForWinTests(unittest.TestCase):
    def test_beating_the_bot_is_worth_less_than_beating_a_member(self) -> None:
        self.assertEqual(amount_for_win(opponent_is_bot=False), config.XP_PER_WIN)
        self.assertEqual(amount_for_win(opponent_is_bot=True), config.XP_PER_BOT_WIN)
        self.assertLess(config.XP_PER_BOT_WIN, config.XP_PER_WIN)


class RewardWinTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = ExperienceStore(Path(directory.name) / "xp.db")
        self.winner = SimpleNamespace(id=10, display_name="Alice", guild=SimpleNamespace(id=1))
        self.channel = mock.Mock(send=mock.AsyncMock())

    async def test_adds_xp_and_returns_a_note(self) -> None:
        note = await reward_win(self.store, self.channel, self.winner, 40)
        self.assertEqual(note, "+40 XP")
        self.assertEqual(await self.store.get(1, 10), 40)
        self.channel.send.assert_not_awaited()

    async def test_announces_a_level_up_without_pinging(self) -> None:
        note = await reward_win(self.store, self.channel, self.winner, 120)
        self.assertEqual(note, "+120 XP · Level 1")
        self.channel.send.assert_awaited_once()
        self.assertIn("**Alice** reached level 1", self.channel.send.await_args.args[0])
        mentions = self.channel.send.await_args.kwargs["allowed_mentions"]
        self.assertFalse(mentions.users)

    async def test_wins_accumulate_toward_a_level_up(self) -> None:
        await reward_win(self.store, self.channel, self.winner, 60)
        self.channel.send.assert_not_awaited()
        await reward_win(self.store, self.channel, self.winner, 60)
        self.channel.send.assert_awaited_once()

    async def test_failed_announcement_does_not_lose_the_xp(self) -> None:
        self.channel.send.side_effect = discord.Forbidden(mock.Mock(status=403), "no access")
        note = await reward_win(self.store, self.channel, self.winner, 120)
        self.assertEqual(note, "+120 XP · Level 1")
        self.assertEqual(await self.store.get(1, 10), 120)


if __name__ == "__main__":
    unittest.main()
