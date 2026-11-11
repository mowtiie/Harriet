"""Tests for XP storage."""

import tempfile
import unittest
from pathlib import Path

from features.leveling.store import ExperienceStore


class ExperienceStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "xp.db"
        self.store = ExperienceStore(self.path)

    async def test_unknown_member_has_zero_xp(self) -> None:
        self.assertEqual(await self.store.get(1, 10), 0)

    async def test_add_accumulates_and_returns_the_total(self) -> None:
        self.assertEqual(await self.store.add(1, 10, 50), 50)
        self.assertEqual(await self.store.add(1, 10, 30), 80)
        self.assertEqual(await self.store.get(1, 10), 80)

    async def test_xp_is_scoped_to_guild_and_member(self) -> None:
        await self.store.add(1, 10, 50)
        self.assertEqual(await self.store.get(2, 10), 0)
        self.assertEqual(await self.store.get(1, 11), 0)

    async def test_set_replaces_the_total(self) -> None:
        await self.store.add(1, 10, 50)
        await self.store.set(1, 10, 20)
        self.assertEqual(await self.store.get(1, 10), 20)
        await self.store.set(1, 11, 7)
        self.assertEqual(await self.store.get(1, 11), 7)

    async def test_reset_removes_the_member(self) -> None:
        await self.store.add(1, 10, 50)
        await self.store.reset(1, 10)
        self.assertEqual(await self.store.get(1, 10), 0)
        self.assertEqual(await self.store.ranking(1), [])

    async def test_ranking_is_highest_first_with_stable_ties_for_one_guild(self) -> None:
        await self.store.add(1, 30, 10)
        await self.store.add(1, 20, 90)
        await self.store.add(1, 10, 90)
        await self.store.add(2, 99, 999)
        self.assertEqual(await self.store.ranking(1), [(10, 90), (20, 90), (30, 10)])

    async def test_xp_persists_across_store_instances(self) -> None:
        await self.store.add(1, 10, 50)
        self.assertEqual(await ExperienceStore(self.path).get(1, 10), 50)


if __name__ == "__main__":
    unittest.main()
