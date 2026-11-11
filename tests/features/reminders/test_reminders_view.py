"""Tests for reminder text formatting."""

import unittest
from datetime import datetime, timedelta, timezone

from features.reminders.reminders_view import (
    LATE_AFTER,
    MAX_TEXT_SHOWN,
    build_reminders_view,
    format_delivery,
    format_reminder_line,
    format_reminders,
    shorten,
)
from features.reminders.store import Reminder

DUE = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


def make_reminder(text: str = "stand up") -> Reminder:
    return Reminder(id=4, user_id=9, channel_id=1, text=text, due_at=DUE)


class ShortenTests(unittest.TestCase):
    def test_short_text_is_unchanged(self) -> None:
        self.assertEqual(shorten("hello"), "hello")

    def test_long_text_is_cut_to_the_limit(self) -> None:
        shortened = shorten("x" * 500)
        self.assertEqual(len(shortened), MAX_TEXT_SHOWN)
        self.assertTrue(shortened.endswith("..."))


class FormatRemindersTests(unittest.TestCase):
    def test_no_reminders(self) -> None:
        self.assertEqual(format_reminders([]), "You have no pending reminders.")

    def test_line_shows_id_time_and_text(self) -> None:
        line = format_reminder_line(make_reminder())
        self.assertTrue(line.startswith("`#4` <t:"))
        self.assertTrue(line.endswith(":R> · stand up"))


class FormatDeliveryTests(unittest.TestCase):
    def test_on_time_reminder_mentions_the_user(self) -> None:
        self.assertEqual(format_delivery(make_reminder(), DUE), "<@9> Reminder: stand up")

    def test_small_delay_is_not_called_out(self) -> None:
        self.assertNotIn("late", format_delivery(make_reminder(), DUE + LATE_AFTER))

    def test_late_reminder_says_so(self) -> None:
        message = format_delivery(make_reminder(), DUE + LATE_AFTER + timedelta(seconds=1))
        self.assertIn("arrived late", message)
        self.assertTrue(message.startswith("<@9> Reminder: stand up\n-# "))


class BuildRemindersViewTests(unittest.TestCase):
    def test_view_builds_into_a_valid_payload(self) -> None:
        self.assertTrue(build_reminders_view([make_reminder()]).to_components())

    def test_empty_list_still_builds(self) -> None:
        self.assertTrue(build_reminders_view([]).to_components())


if __name__ == "__main__":
    unittest.main()
