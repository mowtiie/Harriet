"""Tests for per-server settings storage."""

import tempfile
import unittest
from pathlib import Path

from core.guild_settings import GuildSettings


class GuildSettingsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested" / "settings.db"
        self.settings = GuildSettings(self.path)

    async def test_missing_value_is_none(self) -> None:
        self.assertIsNone(await self.settings.get(1, "volume"))

    async def test_set_then_get(self) -> None:
        await self.settings.set(1, "volume", "30")
        self.assertEqual(await self.settings.get(1, "volume"), "30")

    async def test_set_overwrites_existing_value(self) -> None:
        await self.settings.set(1, "volume", "30")
        await self.settings.set(1, "volume", "70")
        self.assertEqual(await self.settings.get(1, "volume"), "70")

    async def test_guilds_are_isolated(self) -> None:
        await self.settings.set(1, "volume", "30")
        self.assertIsNone(await self.settings.get(2, "volume"))

    async def test_get_int_uses_default_when_unset(self) -> None:
        self.assertEqual(await self.settings.get_int(1, "volume", 50), 50)
        await self.settings.set(1, "volume", "20")
        self.assertEqual(await self.settings.get_int(1, "volume", 50), 20)

    async def test_delete_removes_value(self) -> None:
        await self.settings.set(1, "volume", "30")
        await self.settings.delete(1, "volume")
        self.assertIsNone(await self.settings.get(1, "volume"))

    async def test_values_persist_across_instances(self) -> None:
        await self.settings.set(1, "volume", "30")
        self.assertEqual(await GuildSettings(self.path).get(1, "volume"), "30")


if __name__ == "__main__":
    unittest.main()
