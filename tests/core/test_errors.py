"""Tests for user-facing error messages."""

import inspect
import unittest

from discord.ext import commands

from core.errors import describe_error
from games.errors import FunError
from modtools.errors import ModerationError
from playback.errors import VoiceStateError
from utilities.errors import UtilityError


class DescribeErrorTests(unittest.TestCase):
    def test_owner_only(self) -> None:
        self.assertIn("owner", describe_error(commands.NotOwner()))

    def test_no_private_message(self) -> None:
        self.assertIn("server", describe_error(commands.NoPrivateMessage()))

    def test_bot_missing_permissions_names_them(self) -> None:
        message = describe_error(commands.BotMissingPermissions(["manage_messages"]))
        self.assertIn("manage_messages", message)

    def test_missing_argument_names_parameter(self) -> None:
        param = commands.Parameter("amount", inspect.Parameter.POSITIONAL_ONLY)
        message = describe_error(commands.MissingRequiredArgument(param))
        self.assertIn("amount", message)

    def test_bad_literal_lists_choices(self) -> None:
        param = commands.Parameter("status", inspect.Parameter.POSITIONAL_ONLY)
        error = commands.BadLiteralArgument(param, ("online", "idle"), [])
        message = describe_error(error)
        self.assertIn("online", message)
        self.assertIn("idle", message)

    def test_voice_state_error_shows_its_own_message(self) -> None:
        self.assertEqual(describe_error(VoiceStateError("Join a voice channel first.")), "Join a voice channel first.")

    def test_moderation_error_shows_its_own_message(self) -> None:
        self.assertEqual(describe_error(ModerationError("Nope.")), "Nope.")

    def test_utility_error_shows_its_own_message(self) -> None:
        self.assertEqual(describe_error(UtilityError("Too many.")), "Too many.")

    def test_fun_error_shows_its_own_message(self) -> None:
        self.assertEqual(describe_error(FunError("Pick a person.")), "Pick a person.")

    def test_unexpected_error_returns_none(self) -> None:
        self.assertIsNone(describe_error(RuntimeError("boom")))


if __name__ == "__main__":
    unittest.main()
