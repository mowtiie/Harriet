import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

from features.devtools.status import format_size

MAX_BACKUP_BYTES = 8 * 1024 * 1024


class BackupError(ValueError):
    """The database can't be backed up right now; the message says why."""


def backup_filename(moment: datetime) -> str:
    return f"harriet-{moment:%Y%m%d-%H%M%S}.db"


def snapshot_database(path: Path, max_bytes: int = MAX_BACKUP_BYTES) -> bytes:
    """A consistent copy of the database, taken even while the bot is using it.

    The original is opened read-only, so this can't create or change anything.
    """
    if not path.is_file():
        raise BackupError(f"There's no database file yet ({path.name}), so nothing to back up.")
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / path.name
        source_uri = f"{path.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source:
            with closing(sqlite3.connect(target)) as copy:
                source.backup(copy)
        size = target.stat().st_size
        if size > max_bytes:
            raise BackupError(
                f"The database is {format_size(size)}, over the {format_size(max_bytes)} "
                "limit for sending through Discord."
            )
        return target.read_bytes()
