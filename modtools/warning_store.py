import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from database import transaction

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""
INSERT_SQL = """
INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at)
VALUES (?, ?, ?, ?, ?)
"""
COUNT_SQL = "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?"
LIST_SQL = """
SELECT id, moderator_id, reason, created_at FROM warnings
WHERE guild_id = ? AND user_id = ? ORDER BY id
"""
DELETE_SQL = "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?"


@dataclass(frozen=True)
class WarningRecord:
    id: int
    moderator_id: int
    reason: str
    created_at: datetime


class WarningStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with transaction(path) as connection:
            connection.execute(CREATE_TABLE_SQL)

    async def add(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        """Returns how many warnings the user has after this one."""
        return await asyncio.to_thread(self._add, guild_id, user_id, moderator_id, reason)

    async def list_for(self, guild_id: int, user_id: int) -> list[WarningRecord]:
        return await asyncio.to_thread(self._list_for, guild_id, user_id)

    async def clear(self, guild_id: int, user_id: int) -> int:
        return await asyncio.to_thread(self._clear, guild_id, user_id)

    def _add(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with transaction(self._path) as connection:
            connection.execute(INSERT_SQL, (guild_id, user_id, moderator_id, reason, created_at))
            return connection.execute(COUNT_SQL, (guild_id, user_id)).fetchone()[0]

    def _list_for(self, guild_id: int, user_id: int) -> list[WarningRecord]:
        with transaction(self._path) as connection:
            rows = connection.execute(LIST_SQL, (guild_id, user_id)).fetchall()
        return [
            WarningRecord(row_id, moderator_id, reason, datetime.fromisoformat(created_at))
            for row_id, moderator_id, reason, created_at in rows
        ]

    def _clear(self, guild_id: int, user_id: int) -> int:
        with transaction(self._path) as connection:
            return connection.execute(DELETE_SQL, (guild_id, user_id)).rowcount
