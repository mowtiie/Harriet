"""Tests for warning storage."""

import tempfile
import unittest
from pathlib import Path

from features.modtools.warning_store import WarningStore


class WarningStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = WarningStore(Path(self.directory.name) / "warnings.db")

    async def test_add_returns_running_total(self) -> None:
        self.assertEqual(await self.store.add(1, 10, 99, "first"), 1)
        self.assertEqual(await self.store.add(1, 10, 99, "second"), 2)

    async def test_list_returns_warnings_oldest_first(self) -> None:
        await self.store.add(1, 10, 99, "first")
        await self.store.add(1, 10, 98, "second")
        records = await self.store.list_for(1, 10)
        self.assertEqual([r.reason for r in records], ["first", "second"])
        self.assertEqual([r.moderator_id for r in records], [99, 98])
        self.assertIsNotNone(records[0].created_at.tzinfo)

    async def test_warnings_are_scoped_to_guild_and_user(self) -> None:
        await self.store.add(1, 10, 99, "here")
        self.assertEqual(await self.store.list_for(2, 10), [])
        self.assertEqual(await self.store.list_for(1, 11), [])

    async def test_clear_removes_only_that_users_warnings(self) -> None:
        await self.store.add(1, 10, 99, "a")
        await self.store.add(1, 10, 99, "b")
        await self.store.add(1, 11, 99, "other")
        self.assertEqual(await self.store.clear(1, 10), 2)
        self.assertEqual(await self.store.list_for(1, 10), [])
        self.assertEqual(len(await self.store.list_for(1, 11)), 1)

    async def test_clear_with_nothing_stored_returns_zero(self) -> None:
        self.assertEqual(await self.store.clear(1, 10), 0)


if __name__ == "__main__":
    unittest.main()
