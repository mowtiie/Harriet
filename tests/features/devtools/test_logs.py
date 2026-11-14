"""Tests for reading the bot's log."""

import tempfile
import unittest
from pathlib import Path

from features.devtools.logs import (
    MAX_INLINE_CHARS,
    MAX_LINES,
    MAX_SUMMARY_CHARS,
    build_log_reply,
    clamp_lines,
    error_entries,
    read_log_tail,
    split_entries,
    summarize_error,
)

LOG = "\n".join(
    [
        "[2026-11-14 17:07:04] [INFO    ] discord.client: logging in using static token",
        "[2026-11-14 17:07:05] [INFO    ] bot: Loaded cog: cogs.games",
        "[2026-11-14 17:08:10] [ERROR   ] bot: Failed to load cog: cogs.broken",
        "Traceback (most recent call last):",
        '  File "bot.py", line 74, in load_cogs',
        "SyntaxError: invalid syntax",
        "[2026-11-14 17:09:00] [WARNING ] cogs.music: Slow track",
        "[2026-11-14 17:10:30] [CRITICAL] bot: Out of memory",
    ]
)


class SplitEntriesTests(unittest.TestCase):
    def test_a_traceback_stays_with_the_record_that_caused_it(self) -> None:
        entries = split_entries(LOG)
        self.assertEqual(len(entries), 5)
        self.assertEqual(len(entries[2].splitlines()), 4)
        self.assertTrue(entries[2].endswith("SyntaxError: invalid syntax"))

    def test_text_that_does_not_start_with_a_record_still_forms_an_entry(self) -> None:
        self.assertEqual(split_entries("  File x\nstray"), ["  File x\nstray"])
        self.assertEqual(split_entries(""), [])

    def test_only_errors_and_criticals_are_kept_with_their_tracebacks(self) -> None:
        errors = error_entries(LOG)
        self.assertEqual(len(errors), 2)
        self.assertIn("Traceback", errors[0])
        self.assertIn("Out of memory", errors[1])

    def test_the_level_name_must_match_not_just_appear_in_the_message(self) -> None:
        line = "[2026-11-14 17:07:05] [INFO    ] bot: an ERROR was handled"
        self.assertEqual(error_entries(line), [])


class SummarizeErrorTests(unittest.TestCase):
    def test_keeps_the_time_and_message_of_the_first_line(self) -> None:
        entry = error_entries(LOG)[0]
        self.assertEqual(summarize_error(entry), "17:08:10 bot: Failed to load cog: cogs.broken")

    def test_long_messages_are_shortened_and_backticks_removed(self) -> None:
        entry = "[2026-11-14 17:07:05] [ERROR   ] bot: `" + "x" * 500
        summary = summarize_error(entry)
        self.assertEqual(len(summary), MAX_SUMMARY_CHARS)
        self.assertTrue(summary.endswith("…"))
        self.assertNotIn("`", summary)

    def test_a_line_that_is_not_a_record_is_used_as_is(self) -> None:
        self.assertEqual(summarize_error("weird line"), "weird line")


class BuildLogReplyTests(unittest.TestCase):
    def test_the_last_lines_are_shown_in_a_code_block(self) -> None:
        reply = build_log_reply(LOG, lines=2, errors_only=False)
        self.assertIsNone(reply.attachment)
        self.assertIn("Last 2 line(s)", reply.message)
        self.assertIn("```\n[2026-11-14 17:09:00]", reply.message)
        self.assertNotIn("Loaded cog", reply.message)

    def test_errors_only_keeps_whole_records(self) -> None:
        reply = build_log_reply(LOG, lines=50, errors_only=True)
        self.assertIn("of errors", reply.message)
        self.assertIn("SyntaxError: invalid syntax", reply.message)
        self.assertNotIn("WARNING", reply.message)
        self.assertNotIn("Loaded cog", reply.message)

    def test_an_empty_log_or_no_errors_gets_a_plain_answer(self) -> None:
        self.assertEqual(build_log_reply("", 10, False).message, "The log is empty.")
        quiet = "[2026-11-14 17:07:05] [INFO    ] bot: fine"
        self.assertEqual(
            build_log_reply(quiet, 10, True).message, "No errors since the last start."
        )

    def test_triple_backticks_in_the_log_cannot_break_out_of_the_block(self) -> None:
        text = "[2026-11-14 17:07:05] [INFO    ] bot: ```@everyone```"
        reply = build_log_reply(text, 5, False)
        self.assertEqual(reply.message.count("```"), 2)

    def test_output_that_does_not_fit_in_a_message_becomes_a_file(self) -> None:
        record = "[2026-11-14 17:07:05] [INFO    ] bot: line {} " + "x" * 60
        text = "\n".join(record.format(n) for n in range(80))
        reply = build_log_reply(text, 80, False)
        self.assertGreater(len(text), MAX_INLINE_CHARS)
        self.assertIn("as a file", reply.message)
        self.assertNotIn("```", reply.message)
        self.assertEqual(reply.attachment, text)

    def test_the_line_count_is_kept_within_sensible_limits(self) -> None:
        self.assertEqual(clamp_lines(0), 1)
        self.assertEqual(clamp_lines(-5), 1)
        self.assertEqual(clamp_lines(10_000), MAX_LINES)
        self.assertEqual(clamp_lines(40), 40)


class ReadLogTailTests(unittest.TestCase):
    def test_a_missing_file_reads_as_empty(self) -> None:
        self.assertEqual(read_log_tail(Path("does-not-exist.log")), "")

    def test_a_small_file_is_read_whole(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.log"
            path.write_text(LOG, encoding="utf-8")
            self.assertEqual(read_log_tail(path), LOG)

    def test_a_big_file_gives_only_the_end_starting_on_a_whole_line(self) -> None:
        record = "[2026-11-14 17:07:05] [INFO    ] bot: line {:04d}"
        lines = [record.format(number) for number in range(500)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.log"
            path.write_text("\n".join(lines), encoding="utf-8")
            tail = read_log_tail(path, max_bytes=1000)
        self.assertLess(len(tail), 1000)
        self.assertTrue(tail.startswith("[2026-11-14"))
        self.assertTrue(tail.endswith("line 0499"))

    def test_bytes_that_are_not_utf8_do_not_crash_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.log"
            path.write_bytes(b"[2026-11-14 17:07:05] [INFO    ] bot: caf\xe9")
            self.assertIn("bot: caf", read_log_tail(path))


if __name__ == "__main__":
    unittest.main()
