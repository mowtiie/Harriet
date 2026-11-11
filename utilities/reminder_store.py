import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from database import transaction

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    due_at REAL NOT NULL
)
"""
INSERT_SQL = "INSERT INTO reminders (user_id, channel_id, text, due_at) VALUES (?, ?, ?, ?)"
COUNT_SQL = "SELECT COUNT(*) FROM reminders WHERE user_id = ?"
SELECT_SQL = "SELECT id, user_id, channel_id, text, due_at FROM reminders"
LIST_SQL = f"{SELECT_SQL} WHERE user_id = ? ORDER BY due_at"
DUE_SQL = f"{SELECT_SQL} WHERE due_at <= ? ORDER BY due_at"
DELETE_SQL = "DELETE FROM reminders WHERE id = ?"
DELETE_OWNED_SQL = "DELETE FROM reminders WHERE id = ? AND user_id = ?"


@dataclass(frozen=True)
class Reminder:
    id: int
    user_id: int
    channel_id: int
    text: str
    due_at: datetime


def _to_reminder(row: tuple) -> Reminder:
    reminder_id, user_id, channel_id, text, due_at = row
    due = datetime.fromtimestamp(due_at, timezone.utc)
    return Reminder(reminder_id, user_id, channel_id, text, due)


class ReminderStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with transaction(path) as connection:
            connection.execute(CREATE_TABLE_SQL)

    async def add(self, user_id: int, channel_id: int, text: str, due_at: datetime) -> int:
        return await asyncio.to_thread(self._add, user_id, channel_id, text, due_at)

    async def count_for(self, user_id: int) -> int:
        return await asyncio.to_thread(self._count_for, user_id)

    async def list_for(self, user_id: int) -> list[Reminder]:
        return await asyncio.to_thread(self._query, LIST_SQL, (user_id,))

    async def due(self, now: datetime) -> list[Reminder]:
        return await asyncio.to_thread(self._query, DUE_SQL, (now.timestamp(),))

    async def cancel(self, user_id: int, reminder_id: int) -> bool:
        return await asyncio.to_thread(self._delete, DELETE_OWNED_SQL, (reminder_id, user_id))

    async def complete(self, reminder_id: int) -> None:
        await asyncio.to_thread(self._delete, DELETE_SQL, (reminder_id,))

    def _add(self, user_id: int, channel_id: int, text: str, due_at: datetime) -> int:
        with transaction(self._path) as connection:
            cursor = connection.execute(INSERT_SQL, (user_id, channel_id, text, due_at.timestamp()))
            return cursor.lastrowid

    def _count_for(self, user_id: int) -> int:
        with transaction(self._path) as connection:
            return connection.execute(COUNT_SQL, (user_id,)).fetchone()[0]

    def _query(self, sql: str, parameters: tuple) -> list[Reminder]:
        with transaction(self._path) as connection:
            return [_to_reminder(row) for row in connection.execute(sql, parameters).fetchall()]

    def _delete(self, sql: str, parameters: tuple) -> bool:
        with transaction(self._path) as connection:
            return connection.execute(sql, parameters).rowcount > 0
