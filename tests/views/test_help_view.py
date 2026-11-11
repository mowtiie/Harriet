"""Tests for help text formatting."""

import unittest

from views.help_data import CategoryHelp, CommandHelp
from views.help_view import (
    command_label,
    format_category_summary,
    format_command_block,
    format_usage,
)

CLEAR = CommandHelp(
    name="clear",
    description="Delete messages.",
    signature="[amount=5]",
    examples=("clear", "clear 10"),
    category_name="Moderation",
)
PING = CommandHelp("ping", "Pong.", "", (), "General")


class CommandLabelTests(unittest.TestCase):
    def test_uses_slash_mention_when_available(self) -> None:
        self.assertEqual(command_label(CLEAR, {"clear": "</clear:1>"}), "</clear:1>")

    def test_falls_back_to_code_formatted_name(self) -> None:
        self.assertEqual(command_label(CLEAR, {}), "`/clear`")


class FormatUsageTests(unittest.TestCase):
    def test_includes_signature_for_both_forms(self) -> None:
        self.assertEqual(format_usage(CLEAR, "do "), "`/clear [amount=5]` · `do clear [amount=5]`")

    def test_omits_signature_when_command_has_no_arguments(self) -> None:
        self.assertEqual(format_usage(PING, "do "), "`/ping` · `do ping`")


class FormatCommandBlockTests(unittest.TestCase):
    def test_lists_heading_description_usage_and_examples(self) -> None:
        block = format_command_block(CLEAR, "do ", {}, "###")
        self.assertEqual(
            block.splitlines(),
            [
                "### `/clear`",
                "Delete messages.",
                "> **Usage** · `/clear [amount=5]` · `do clear [amount=5]`",
                "> **Examples** · `do clear` · `do clear 10`",
            ],
        )

    def test_skips_examples_line_when_there_are_none(self) -> None:
        self.assertNotIn("Examples", format_command_block(PING, "do ", {}, "###"))


class FormatCategorySummaryTests(unittest.TestCase):
    def test_lists_commands_under_heading(self) -> None:
        category = CategoryHelp("General", "Basics.", (PING, CLEAR))
        self.assertEqual(
            format_category_summary(category, {}).splitlines(),
            ["### General", "Basics.", "`/ping` · `/clear`"],
        )

    def test_omits_blank_description(self) -> None:
        category = CategoryHelp("General", "", (PING,))
        self.assertEqual(len(format_category_summary(category, {}).splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
