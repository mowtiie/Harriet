"""Tests for mod-log and warnings formatting."""

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from modtools.models import ModAction
from modtools.warning_store import WarningRecord
from views.modlog_view import format_modlog_fields
from views.warnings_view import MAX_WARNINGS_SHOWN, format_warnings


def make_action(duration: timedelta | None = None) -> ModAction:
    return ModAction(
        "Timeout",
        "timed out",
        SimpleNamespace(name="Server"),
        SimpleNamespace(id=1, mention="<@1>"),
        SimpleNamespace(id=2, mention="<@2>"),
        "spam",
        duration,
    )


def make_record(record_id: int) -> WarningRecord:
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return WarningRecord(record_id, 1, f"reason {record_id}", created)


class FormatModlogFieldsTests(unittest.TestCase):
    def test_lists_member_moderator_and_reason(self) -> None:
        self.assertEqual(
            format_modlog_fields(make_action()).splitlines(),
            ["**Member** · <@2> (`2`)", "**Moderator** · <@1>", "**Reason** · spam"],
        )

    def test_includes_duration_before_reason(self) -> None:
        lines = format_modlog_fields(make_action(timedelta(hours=2))).splitlines()
        self.assertEqual(lines[2:], ["**Duration** · 2h", "**Reason** · spam"])


class FormatWarningsTests(unittest.TestCase):
    def test_no_warnings(self) -> None:
        self.assertEqual(format_warnings([]), "No warnings.")

    def test_lists_each_warning_with_id_reason_and_moderator(self) -> None:
        line = format_warnings([make_record(3)])
        self.assertIn("`#3`", line)
        self.assertIn("reason 3", line)
        self.assertIn("<@1>", line)

    def test_shows_only_the_latest_warnings(self) -> None:
        records = [make_record(i) for i in range(1, MAX_WARNINGS_SHOWN + 4)]
        lines = format_warnings(records).splitlines()
        self.assertEqual(len(lines), MAX_WARNINGS_SHOWN + 1)
        self.assertIn("`#4`", lines[0])
        self.assertEqual(lines[-1], "-# 3 older warning(s) not shown")


if __name__ == "__main__":
    unittest.main()
