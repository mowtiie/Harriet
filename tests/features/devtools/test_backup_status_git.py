"""Tests for the database backup, the status text and the git helpers."""

import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from features.devtools.backup import BackupError, backup_filename, snapshot_database
from features.devtools.git_info import current_commit, has_uncommitted_changes
from features.devtools.status import StatusInfo, format_size, format_status


def make_database(directory: str, rows: int = 3) -> Path:
    path = Path(directory) / "harriet.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE warnings (id INTEGER PRIMARY KEY, reason TEXT)")
        connection.executemany(
            "INSERT INTO warnings (reason) VALUES (?)", [(f"reason {n}",) for n in range(rows)]
        )
    return path


def rows_of(data: bytes) -> list[tuple]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "copy.db"
        path.write_bytes(data)
        with closing(sqlite3.connect(path)) as connection:
            return connection.execute("SELECT reason FROM warnings ORDER BY id").fetchall()


class SnapshotDatabaseTests(unittest.TestCase):
    def test_the_copy_holds_the_same_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = snapshot_database(make_database(directory))
        self.assertEqual(rows_of(data), [("reason 0",), ("reason 1",), ("reason 2",)])

    def test_the_original_is_left_exactly_as_it_was(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = make_database(directory)
            before = path.read_bytes()
            snapshot_database(path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([item.name for item in Path(directory).iterdir()], ["harriet.db"])

    def test_a_copy_is_consistent_even_with_the_bot_holding_the_file_open(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = make_database(directory)
            with closing(sqlite3.connect(path)) as writer:
                writer.execute("INSERT INTO warnings (reason) VALUES ('late')")
                writer.commit()
                data = snapshot_database(path)
        self.assertIn(("late",), rows_of(data))

    def test_a_missing_database_is_reported_not_created(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "harriet.db"
            with self.assertRaises(BackupError) as caught:
                snapshot_database(path)
            self.assertIn("no database file", str(caught.exception))
            self.assertFalse(path.exists())

    def test_a_database_over_the_limit_is_refused_with_its_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(BackupError) as caught:
                snapshot_database(make_database(directory), max_bytes=1024)
        self.assertIn("limit", str(caught.exception))

    def test_a_file_that_is_not_a_database_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "harriet.db"
            path.write_bytes(b"this is not sqlite" * 100)
            with self.assertRaises(sqlite3.DatabaseError):
                snapshot_database(path)

    def test_the_filename_carries_the_time(self) -> None:
        moment = datetime(2026, 11, 14, 17, 5, 9, tzinfo=timezone.utc)
        self.assertEqual(backup_filename(moment), "harriet-20261114-170509.db")


class FormatSizeTests(unittest.TestCase):
    def test_sizes_read_naturally(self) -> None:
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(512), "512 B")
        self.assertEqual(format_size(32768), "32.0 KB")
        self.assertEqual(format_size(1536 * 1024), "1.5 MB")
        self.assertEqual(format_size(3 * 1024**3), "3.0 GB")
        self.assertEqual(format_size(5000 * 1024**3), "5000.0 GB")


def make_info(**changes: object) -> StatusInfo:
    values = dict(
        uptime=timedelta(hours=2, minutes=14, seconds=5),
        latency_ms=48,
        guild_count=1,
        voice_connections=0,
        active_games=2,
        commit="52b9fb3",
        started_commit="52b9fb3",
        has_uncommitted_changes=False,
        loaded_cogs=17,
        unloaded_cogs=(),
        command_count=56,
        database_bytes=32768,
        error_count=0,
        last_error=None,
    )
    values.update(changes)
    return StatusInfo(**values)


class FormatStatusTests(unittest.TestCase):
    def test_a_healthy_bot(self) -> None:
        lines = format_status(make_info()).splitlines()
        self.assertEqual(lines[0], "**Status**")
        self.assertEqual(lines[1], "Uptime **2h 14m 5s** · Latency **48 ms** · Servers **1**")
        self.assertEqual(lines[2], "Games in progress **2** · Voice connections **0**")
        self.assertEqual(lines[3], "Commit `52b9fb3`")
        self.assertEqual(lines[4], "Cogs **17 loaded** · Slash commands **56**")
        self.assertEqual(lines[5], "Database **32.0 KB**")
        self.assertEqual(lines[6], "Errors since start **0**")
        self.assertEqual(len(lines), 7)

    def test_running_old_code_with_local_edits_is_visible(self) -> None:
        text = format_status(
            make_info(commit="def5678", started_commit="abc1234", has_uncommitted_changes=True)
        )
        self.assertIn("Commit `def5678` (started on `abc1234`) · uncommitted changes", text)

    def test_cogs_that_are_not_loaded_are_named(self) -> None:
        text = format_status(make_info(unloaded_cogs=("cogs.new", "cogs.broken")))
        self.assertIn("not loaded: `cogs.new`, `cogs.broken`", text)

    def test_errors_show_the_last_one(self) -> None:
        text = format_status(make_info(error_count=3, last_error="17:08:10 bot: boom"))
        self.assertIn("Errors since start **3**\n-# Last: `17:08:10 bot: boom`", text)

    def test_missing_git_and_database_are_explained(self) -> None:
        text = format_status(make_info(commit=None, database_bytes=None))
        self.assertIn("Commit **unknown** (git isn't available)", text)
        self.assertIn("Database **no file yet**", text)


class GitInfoTests(unittest.TestCase):
    def run_git(self, stdout: str = "", error: Exception | None = None):
        completed = subprocess.CompletedProcess([], 0, stdout=stdout)
        return mock.patch(
            "features.devtools.git_info.subprocess.run", side_effect=error, return_value=completed
        )

    def test_the_short_commit_is_read_from_git(self) -> None:
        with self.run_git("52b9fb3\n") as run:
            self.assertEqual(current_commit(Path(".")), "52b9fb3")
        self.assertEqual(run.call_args.args[0], ["git", "rev-parse", "--short", "HEAD"])

    def test_missing_git_or_a_failed_command_gives_none(self) -> None:
        for error in (FileNotFoundError(), subprocess.CalledProcessError(128, "git"),
                      subprocess.TimeoutExpired("git", 5)):
            with self.subTest(error=type(error).__name__), self.run_git(error=error):
                self.assertIsNone(current_commit(Path(".")))
                self.assertIsNone(has_uncommitted_changes(Path(".")))

    def test_an_empty_answer_is_not_a_commit(self) -> None:
        with self.run_git(""):
            self.assertIsNone(current_commit(Path(".")))

    def test_uncommitted_changes_are_told_apart_from_a_clean_tree(self) -> None:
        with self.run_git(" M cogs/games.py\n"):
            self.assertTrue(has_uncommitted_changes(Path(".")))
        with self.run_git(""):
            self.assertFalse(has_uncommitted_changes(Path(".")))


if __name__ == "__main__":
    unittest.main()
