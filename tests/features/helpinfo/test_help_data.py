"""Tests for help data helpers."""

import unittest

from discord.ext import commands

from features.helpinfo.help_data import (
    DEFAULT_CATEGORY_NAME,
    NO_DESCRIPTION,
    describe_command,
    find_command,
    group_into_categories,
    matching_command_names,
)


class FakeCog(commands.Cog, description="Fake cog."):
    pass


async def _callback(ctx: commands.Context, amount: int = 5) -> None:
    return None


def make_command(name: str, cog: commands.Cog | None = None, **kwargs: object) -> commands.Command:
    command = commands.Command(_callback, name=name, **kwargs)
    command.cog = cog
    return command


class DescribeCommandTests(unittest.TestCase):
    def test_reads_description_signature_and_examples(self) -> None:
        command = make_command(
            "clear", FakeCog(), description="Delete.", extras={"examples": ["clear 3"]}
        )
        described = describe_command(command)
        self.assertEqual(described.name, "clear")
        self.assertEqual(described.description, "Delete.")
        self.assertEqual(described.signature, "[amount=5]")
        self.assertEqual(described.examples, ("clear 3",))
        self.assertEqual(described.category_name, "FakeCog")

    def test_falls_back_when_metadata_is_missing(self) -> None:
        described = describe_command(make_command("orphan"))
        self.assertEqual(described.description, NO_DESCRIPTION)
        self.assertEqual(described.examples, ())
        self.assertEqual(described.category_name, DEFAULT_CATEGORY_NAME)


class GroupIntoCategoriesTests(unittest.TestCase):
    def test_groups_by_cog_and_sorts_commands(self) -> None:
        cog = FakeCog()
        categories = group_into_categories(
            [make_command("zeta", cog), make_command("alpha", cog), make_command("loose")]
        )
        self.assertEqual([c.name for c in categories], ["FakeCog", DEFAULT_CATEGORY_NAME])
        self.assertEqual([c.name for c in categories[0].commands], ["alpha", "zeta"])
        self.assertEqual(categories[0].description, "Fake cog.")

    def test_empty_input_gives_no_categories(self) -> None:
        self.assertEqual(group_into_categories([]), [])


class FindCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = [make_command("ping"), make_command("clear")]

    def test_matches_ignoring_case_whitespace_and_slash(self) -> None:
        self.assertIs(find_command(self.candidates, " /PING "), self.candidates[0])

    def test_unknown_name_returns_none(self) -> None:
        self.assertIsNone(find_command(self.candidates, "nope"))


class MatchingCommandNamesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = [
            make_command("ping"),
            make_command("clear"),
            make_command("secret", hidden=True),
        ]

    def test_filters_by_substring_and_skips_hidden(self) -> None:
        self.assertEqual(matching_command_names(self.candidates, "", 25), ["clear", "ping"])
        self.assertEqual(matching_command_names(self.candidates, "IN", 25), ["ping"])

    def test_respects_limit(self) -> None:
        self.assertEqual(matching_command_names(self.candidates, "", 1), ["clear"])


if __name__ == "__main__":
    unittest.main()
