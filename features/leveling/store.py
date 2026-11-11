import asyncio
from pathlib import Path

from core.database import transaction

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS experience (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    xp INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
)
"""
ADD_SQL = """
INSERT INTO experience (guild_id, user_id, xp) VALUES (?, ?, ?)
ON CONFLICT (guild_id, user_id) DO UPDATE SET xp = xp + excluded.xp
"""
SET_SQL = """
INSERT INTO experience (guild_id, user_id, xp) VALUES (?, ?, ?)
ON CONFLICT (guild_id, user_id) DO UPDATE SET xp = excluded.xp
"""
GET_SQL = "SELECT xp FROM experience WHERE guild_id = ? AND user_id = ?"
RANKING_SQL = "SELECT user_id, xp FROM experience WHERE guild_id = ? ORDER BY xp DESC, user_id"
DELETE_SQL = "DELETE FROM experience WHERE guild_id = ? AND user_id = ?"


class ExperienceStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with transaction(path) as connection:
            connection.execute(CREATE_TABLE_SQL)

    async def add(self, guild_id: int, user_id: int, amount: int) -> int:
        """Returns the member's total XP after adding."""
        return await asyncio.to_thread(self._add, guild_id, user_id, amount)

    async def get(self, guild_id: int, user_id: int) -> int:
        return await asyncio.to_thread(self._get, guild_id, user_id)

    async def set(self, guild_id: int, user_id: int, xp: int) -> None:
        await asyncio.to_thread(self._execute, SET_SQL, (guild_id, user_id, xp))

    async def reset(self, guild_id: int, user_id: int) -> None:
        await asyncio.to_thread(self._execute, DELETE_SQL, (guild_id, user_id))

    async def ranking(self, guild_id: int) -> list[tuple[int, int]]:
        return await asyncio.to_thread(self._ranking, guild_id)

    def _add(self, guild_id: int, user_id: int, amount: int) -> int:
        with transaction(self._path) as connection:
            connection.execute(ADD_SQL, (guild_id, user_id, amount))
            return connection.execute(GET_SQL, (guild_id, user_id)).fetchone()[0]

    def _get(self, guild_id: int, user_id: int) -> int:
        with transaction(self._path) as connection:
            row = connection.execute(GET_SQL, (guild_id, user_id)).fetchone()
        return 0 if row is None else row[0]

    def _ranking(self, guild_id: int) -> list[tuple[int, int]]:
        with transaction(self._path) as connection:
            return connection.execute(RANKING_SQL, (guild_id,)).fetchall()

    def _execute(self, sql: str, parameters: tuple) -> None:
        with transaction(self._path) as connection:
            connection.execute(sql, parameters)
