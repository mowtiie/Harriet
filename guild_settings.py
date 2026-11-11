import asyncio
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

VOLUME_KEY = "volume"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (guild_id, key)
)
"""
SELECT_SQL = "SELECT value FROM guild_settings WHERE guild_id = ? AND key = ?"
UPSERT_SQL = """
INSERT INTO guild_settings (guild_id, key, value) VALUES (?, ?, ?)
ON CONFLICT (guild_id, key) DO UPDATE SET value = excluded.value
"""


class GuildSettings:
    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as connection:
            connection.execute(CREATE_TABLE_SQL)

    async def get(self, guild_id: int, key: str) -> str | None:
        return await asyncio.to_thread(self._get, guild_id, key)

    async def set(self, guild_id: int, key: str, value: str) -> None:
        await asyncio.to_thread(self._set, guild_id, key, value)

    async def get_int(self, guild_id: int, key: str, default: int) -> int:
        raw = await self.get(guild_id, key)
        return default if raw is None else int(raw)

    def _get(self, guild_id: int, key: str) -> str | None:
        with self._transaction() as connection:
            row = connection.execute(SELECT_SQL, (guild_id, key)).fetchone()
        return None if row is None else row[0]

    def _set(self, guild_id: int, key: str, value: str) -> None:
        with self._transaction() as connection:
            connection.execute(UPSERT_SQL, (guild_id, key, value))

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path)) as connection, connection:
            yield connection
