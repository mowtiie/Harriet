"""Tests for reloading cogs without restarting the bot."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import discord
from discord.ext import commands

from core.errors import UserError
from core.reloading import (
    ReloadPlan,
    ReloadReport,
    ReloadResult,
    command_signature,
    describe_failure,
    discover_extensions,
    format_report,
    plan_reload,
    purge_stale_modules,
    reload_extensions,
    restore_unused_modules,
    stale_modules,
)

SELF = "cogs.developer"
AVAILABLE = ["cogs.games", "cogs.music", "cogs.new", SELF]
LOADED = ["cogs.games", "cogs.music", "cogs.removed", SELF]


class DiscoverExtensionsTests(unittest.TestCase):
    def test_lists_public_modules_in_order_and_skips_private_ones(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cogs_dir = Path(directory) / "cogs"
            cogs_dir.mkdir()
            for name in ("music.py", "__init__.py", "_support.py", "games.py", "notes.txt"):
                (cogs_dir / name).write_text("", encoding="utf-8")
            self.assertEqual(discover_extensions(cogs_dir), ["cogs.games", "cogs.music"])


class PlanReloadTests(unittest.TestCase):
    def test_everything_syncs_with_the_files_on_disk(self) -> None:
        plan = plan_reload(AVAILABLE, LOADED, reload_last=SELF)
        self.assertEqual(plan.load, ("cogs.new",))
        self.assertEqual(plan.unload, ("cogs.removed",))
        self.assertEqual(plan.reload, ("cogs.games", "cogs.music", SELF))

    def test_the_named_cog_is_reloaded_last(self) -> None:
        names = ["cogs.a", "cogs.b", "cogs.c"]
        plan = plan_reload(names, names, reload_last="cogs.a")
        self.assertEqual(plan.reload, ("cogs.b", "cogs.c", "cogs.a"))

    def test_a_single_loaded_cog_is_reloaded(self) -> None:
        plan = plan_reload(AVAILABLE, LOADED, "cogs.games")
        self.assertEqual(plan, ReloadPlan(reload=("cogs.games",)))

    def test_a_single_new_cog_is_loaded(self) -> None:
        plan = plan_reload(AVAILABLE, LOADED, "cogs.new")
        self.assertEqual(plan, ReloadPlan(load=("cogs.new",)))

    def test_a_single_deleted_cog_is_unloaded(self) -> None:
        plan = plan_reload(AVAILABLE, LOADED, "cogs.removed")
        self.assertEqual(plan, ReloadPlan(unload=("cogs.removed",)))

    def test_an_unknown_cog_is_refused_with_its_short_name(self) -> None:
        with self.assertRaises(UserError) as caught:
            plan_reload(AVAILABLE, LOADED, "cogs.nope")
        self.assertIn("`nope`", str(caught.exception))


class StaleModuleTests(unittest.TestCase):
    PINNED = {"core.errors", "features.leveling.store", "cogs", "config"}

    def test_picks_project_modules_that_are_not_pinned_or_extensions(self) -> None:
        imported = [
            "core.errors",
            "core.reloading_new",
            "features.games.tictactoe",
            "features.leveling.store",
            "cogs._game_support",
            "cogs.games",
            "views.style",
            "cogs",
            "features",
            "discord.ui",
            "config",
            "unittest.mock",
        ]
        stale = stale_modules(imported, self.PINNED, {"cogs.games"})
        self.assertEqual(
            stale,
            ["cogs._game_support", "core.reloading_new", "features.games.tictactoe", "views.style"],
        )

    def test_modules_holding_state_that_must_outlive_a_reload_are_never_purged(self) -> None:
        imported = ["core.live_views", "core.durations"]
        self.assertEqual(stale_modules(imported, set(), set()), ["core.durations"])

    def test_purging_forgets_only_the_stale_modules(self) -> None:
        modules = {"features.games.rps": object(), "core.errors": object(), "json": object()}
        purged = purge_stale_modules(self.PINNED, set(), modules)
        self.assertEqual(list(purged), ["features.games.rps"])
        self.assertEqual(sorted(modules), ["core.errors", "json"])

    def test_restoring_only_fills_the_gaps_the_reload_left(self) -> None:
        old_rps, old_hangman, fresh_hangman = object(), object(), object()
        modules = {"features.games.hangman": fresh_hangman}
        removed = {"features.games.rps": old_rps, "features.games.hangman": old_hangman}
        restore_unused_modules(removed, modules)
        self.assertIs(modules["features.games.rps"], old_rps)
        self.assertIs(modules["features.games.hangman"], fresh_hangman)


class FakeBot:
    def __init__(self, signatures: list[list[dict]]) -> None:
        self.extensions = {"cogs.games": object()}
        self.unload_extension = mock.AsyncMock()
        self.reload_extension = mock.AsyncMock()
        self.load_extension = mock.AsyncMock()
        self.tree = mock.Mock()
        self.tree.sync = mock.AsyncMock(return_value=[object()] * 3)
        self._signatures = iter(signatures)
        self.tree.get_commands.side_effect = self._next_commands

    def _next_commands(self) -> list[SimpleNamespace]:
        entries = next(self._signatures)
        return [SimpleNamespace(to_dict=lambda tree, e=entry: e) for entry in entries]


SAME = [{"name": "rps"}]
CHANGED = [{"name": "rps"}, {"name": "guess"}]


class ReloadExtensionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_runs_the_plan_in_order_and_reports_each_step(self) -> None:
        bot = FakeBot([SAME, SAME])
        plan = ReloadPlan(load=("cogs.new",), reload=("cogs.games",), unload=("cogs.old",))
        report = await reload_extensions(bot, plan, set())
        bot.unload_extension.assert_awaited_once_with("cogs.old")
        bot.reload_extension.assert_awaited_once_with("cogs.games")
        bot.load_extension.assert_awaited_once_with("cogs.new")
        self.assertEqual(
            [(result.verb, result.extension) for result in report.results],
            [("unload", "cogs.old"), ("reload", "cogs.games"), ("load", "cogs.new")],
        )

    async def test_unchanged_commands_are_not_synced(self) -> None:
        bot = FakeBot([SAME, SAME])
        report = await reload_extensions(bot, ReloadPlan(reload=("cogs.games",)), set())
        bot.tree.sync.assert_not_awaited()
        self.assertIsNone(report.synced)

    async def test_changed_commands_are_synced_once(self) -> None:
        bot = FakeBot([SAME, CHANGED])
        report = await reload_extensions(bot, ReloadPlan(load=("cogs.new",)), set())
        bot.tree.sync.assert_awaited_once()
        self.assertEqual(report.synced, 3)
        self.assertFalse(report.sync_failed)

    async def test_a_failed_reload_is_reported_and_the_rest_still_run(self) -> None:
        bot = FakeBot([SAME, SAME])
        bot.reload_extension.side_effect = [
            commands.ExtensionFailed("cogs.games", SyntaxError("bad syntax")),
            None,
        ]
        plan = ReloadPlan(reload=("cogs.games", "cogs.music"))
        report = await reload_extensions(bot, plan, set())
        self.assertEqual(bot.reload_extension.await_count, 2)
        self.assertIn("SyntaxError: bad syntax", report.results[0].error)
        self.assertIsNone(report.results[1].error)

    async def test_a_failed_sync_is_reported_not_raised(self) -> None:
        bot = FakeBot([SAME, CHANGED])
        bot.tree.sync.side_effect = discord.HTTPException(mock.Mock(status=500, reason="x"), "boom")
        report = await reload_extensions(bot, ReloadPlan(load=("cogs.new",)), set())
        self.assertTrue(report.sync_failed)
        self.assertIsNone(report.synced)

    async def test_command_signature_is_sorted_by_name(self) -> None:
        bot = FakeBot([[{"name": "b"}, {"name": "a"}]])
        self.assertEqual([entry["name"] for entry in command_signature(bot)], ["a", "b"])


class FormatReportTests(unittest.TestCase):
    def test_success_failure_and_sync_lines(self) -> None:
        report = ReloadReport(
            (
                ReloadResult("cogs.games", "reload"),
                ReloadResult("cogs.new", "load"),
                ReloadResult("cogs.old", "unload"),
                ReloadResult("cogs.music", "reload", "SyntaxError: bad"),
                ReloadResult("cogs.fresh", "load", "ImportError: nope"),
            ),
            synced=52,
        )
        self.assertEqual(
            format_report(report).splitlines(),
            [
                "Reloaded `cogs.games`.",
                "Loaded `cogs.new`.",
                "Unloaded `cogs.old`.",
                "Could not reload `cogs.music`: SyntaxError: bad."
                " The previous version is still running.",
                "Could not load `cogs.fresh`: ImportError: nope.",
                "Synced 52 slash commands.",
            ],
        )

    def test_sync_failure_and_empty_reports(self) -> None:
        self.assertIn("sync failed", format_report(ReloadReport((), sync_failed=True)))
        self.assertEqual(format_report(ReloadReport(())), "Nothing to reload.")

    def test_a_long_report_stays_within_discords_message_limit(self) -> None:
        results = tuple(ReloadResult(f"cogs.c{n}", "reload", "x" * 200) for n in range(30))
        self.assertLessEqual(len(format_report(ReloadReport(results))), 2000)

    def test_failures_name_the_underlying_error_and_are_shortened(self) -> None:
        error = commands.ExtensionFailed("cogs.x", ValueError("y" * 500))
        text = describe_failure(error)
        self.assertTrue(text.startswith("ValueError: yyy"))
        self.assertLessEqual(len(text), 200)


if __name__ == "__main__":
    unittest.main()
