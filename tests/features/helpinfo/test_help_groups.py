"""Tests for how cogs are grouped into help categories."""

import importlib
import unittest
from pathlib import Path

from discord.ext import commands

from features.helpinfo.help_data import describe_command, group_into_categories
from features.helpinfo.help_groups import GROUP_BY_COG_NAME, HELP_GROUPS
from tests.features.helpinfo.test_help_data import make_command

COGS_DIR = Path(__file__).resolve().parents[3] / "cogs"


def cog_named(name: str, description: str = "Own blurb.") -> commands.Cog:
    cog_class = type(name, (commands.Cog,), {}, name=name, description=description)
    return cog_class()


def real_cog_names() -> set[str]:
    names = set()
    for path in COGS_DIR.glob("[!_]*.py"):
        module = importlib.import_module(f"cogs.{path.stem}")
        for value in vars(module).values():
            is_cog = isinstance(value, type) and issubclass(value, commands.Cog)
            if is_cog and value is not commands.Cog and value.__module__ == module.__name__:
                names.add(value.__cog_name__)
    return names


class HelpGroupDefinitionTests(unittest.TestCase):
    def test_group_names_are_unique(self) -> None:
        names = [group.name for group in HELP_GROUPS]
        self.assertEqual(len(names), len(set(names)))

    def test_a_cog_belongs_to_exactly_one_group(self) -> None:
        listed = [name for group in HELP_GROUPS for name in group.cog_names]
        self.assertEqual(len(listed), len(set(listed)))

    def test_every_group_has_a_blurb_that_fits_a_menu_option(self) -> None:
        for group in HELP_GROUPS:
            with self.subTest(group=group.name):
                self.assertTrue(0 < len(group.description) <= 100)

    def test_every_real_cog_is_in_a_group(self) -> None:
        self.assertEqual(real_cog_names() - set(GROUP_BY_COG_NAME), set())

    def test_no_group_lists_a_cog_that_does_not_exist(self) -> None:
        self.assertEqual(set(GROUP_BY_COG_NAME) - real_cog_names(), set())


class GroupingTests(unittest.TestCase):
    def test_commands_from_several_cogs_share_one_category(self) -> None:
        games, solo = cog_named("Games"), cog_named("SoloGames")
        categories = group_into_categories(
            [make_command("rps", games), make_command("hangman", solo)]
        )
        self.assertEqual([category.name for category in categories], ["Games"])
        self.assertEqual([c.name for c in categories[0].commands], ["hangman", "rps"])

    def test_a_group_uses_its_own_blurb_instead_of_a_cogs(self) -> None:
        category = group_into_categories([make_command("rps", cog_named("Games"))])[0]
        self.assertIn("XP", category.description)
        self.assertNotEqual(category.description, "Own blurb.")

    def test_categories_follow_the_declared_order(self) -> None:
        music, general = cog_named("Music"), cog_named("General")
        categories = group_into_categories(
            [make_command("play", music), make_command("ping", general)]
        )
        self.assertEqual([category.name for category in categories], ["General", "Music"])

    def test_an_unmapped_cog_keeps_its_own_name_and_blurb_after_the_groups(self) -> None:
        newcomer = cog_named("Newcomer", "A brand new cog.")
        categories = group_into_categories(
            [make_command("fresh", newcomer), make_command("play", cog_named("Music"))]
        )
        self.assertEqual([category.name for category in categories], ["Music", "Newcomer"])
        self.assertEqual(categories[1].description, "A brand new cog.")

    def test_a_command_reports_its_group_as_its_category(self) -> None:
        described = describe_command(make_command("warn", cog_named("Warnings")))
        self.assertEqual(described.category_name, "Moderation")


if __name__ == "__main__":
    unittest.main()
