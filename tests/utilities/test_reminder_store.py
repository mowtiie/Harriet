"""Tests for reminder storage."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from utilities.reminder_store import ReminderStore

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


class ReminderStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ReminderStore(Path(self.directory.name) / "reminders.db")

    async def test_add_returns_ids_and_counts_per_user(self) -> None:
        first = await self.store.add(1, 10, "a", NOW)
        second = await self.store.add(1, 10, "b", NOW)
        await self.store.add(2, 10, "other", NOW)
        self.assertNotEqual(first, second)
        self.assertEqual(await self.store.count_for(1), 2)
        self.assertEqual(await self.store.count_for(2), 1)

    async def test_list_is_sorted_by_due_time_and_scoped_to_the_user(self) -> None:
        await self.store.add(1, 10, "later", NOW + timedelta(hours=2))
        await self.store.add(1, 10, "sooner", NOW + timedelta(hours=1))
        await self.store.add(2, 10, "someone else", NOW)
        reminders = await self.store.list_for(1)
        self.assertEqual([r.text for r in reminders], ["sooner", "later"])

    async def test_round_trips_all_fields(self) -> None:
        reminder_id = await self.store.add(1, 10, "hello", NOW)
        (reminder,) = await self.store.list_for(1)
        self.assertEqual(
            (reminder.id, reminder.user_id, reminder.channel_id, reminder.text, reminder.due_at),
            (reminder_id, 1, 10, "hello", NOW),
        )

    async def test_due_returns_only_reminders_that_are_due(self) -> None:
        await self.store.add(1, 10, "past", NOW - timedelta(minutes=5))
        await self.store.add(1, 10, "exact", NOW)
        await self.store.add(1, 10, "future", NOW + timedelta(minutes=5))
        due = await self.store.due(NOW)
        self.assertEqual([r.text for r in due], ["past", "exact"])

    async def test_cancel_only_removes_the_owners_reminder(self) -> None:
        reminder_id = await self.store.add(1, 10, "mine", NOW)
        self.assertFalse(await self.store.cancel(2, reminder_id))
        self.assertTrue(await self.store.cancel(1, reminder_id))
        self.assertFalse(await self.store.cancel(1, reminder_id))
        self.assertEqual(await self.store.count_for(1), 0)

    async def test_complete_removes_a_delivered_reminder(self) -> None:
        reminder_id = await self.store.add(1, 10, "done", NOW)
        await self.store.complete(reminder_id)
        self.assertEqual(await self.store.due(NOW), [])

    async def test_reminders_survive_a_new_store_instance(self) -> None:
        await self.store.add(1, 10, "persisted", NOW)
        reopened = ReminderStore(Path(self.directory.name) / "reminders.db")
        self.assertEqual(await reopened.count_for(1), 1)


if __name__ == "__main__":
    unittest.main()
