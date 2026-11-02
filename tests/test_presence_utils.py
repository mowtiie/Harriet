"""Tests for presence helpers."""

import unittest

import discord

from presence_utils import build_presence


class BuildPresenceTests(unittest.TestCase):
    def test_maps_known_values(self) -> None:
        status, activity = build_presence("idle", "watching", "the logs")
        self.assertEqual(status, discord.Status.idle)
        self.assertEqual(activity.type, discord.ActivityType.watching)
        self.assertEqual(activity.name, "the logs")

    def test_is_case_insensitive(self) -> None:
        status, activity = build_presence("DND", "Listening", "x")
        self.assertEqual(status, discord.Status.dnd)
        self.assertEqual(activity.type, discord.ActivityType.listening)

    def test_unknown_values_fall_back_to_defaults(self) -> None:
        status, activity = build_presence("away", "streaming", "x")
        self.assertEqual(status, discord.Status.online)
        self.assertEqual(activity.type, discord.ActivityType.playing)


if __name__ == "__main__":
    unittest.main()
