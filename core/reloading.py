import importlib
import logging
import sys
from collections.abc import (
    Awaitable,
    Callable,
    Collection,
    Iterable,
    Mapping,
    MutableMapping,
)
from dataclasses import dataclass
from pathlib import Path

import discord
from discord.ext import commands

from core.errors import UserError

log = logging.getLogger(__name__)

EXTENSION_GLOB = "[!_]*.py"
RELOADABLE_ROOTS = frozenset({"cogs", "core", "features", "views"})
MAX_FAILURE_LENGTH = 200
MAX_REPORT_LENGTH = 1900


def discover_extensions(cogs_dir: Path) -> list[str]:
    return [f"{cogs_dir.name}.{path.stem}" for path in sorted(cogs_dir.glob(EXTENSION_GLOB))]


@dataclass(frozen=True)
class ReloadPlan:
    load: tuple[str, ...] = ()
    reload: tuple[str, ...] = ()
    unload: tuple[str, ...] = ()


def plan_reload(
    available: Iterable[str],
    loaded: Iterable[str],
    requested: str | None = None,
    reload_last: str | None = None,
) -> ReloadPlan:
    available, loaded = set(available), set(loaded)
    if requested is None:
        return ReloadPlan(
            load=tuple(sorted(available - loaded)),
            reload=_with_last_at_the_end(available & loaded, reload_last),
            unload=tuple(sorted(loaded - available)),
        )
    if requested in available:
        if requested in loaded:
            return ReloadPlan(reload=(requested,))
        return ReloadPlan(load=(requested,))
    if requested in loaded:
        return ReloadPlan(unload=(requested,))
    raise UserError(f"There is no cog called `{requested.rsplit('.', 1)[-1]}`.")


def _with_last_at_the_end(names: Iterable[str], last: str | None) -> tuple[str, ...]:
    return tuple(sorted(names, key=lambda name: (name == last, name)))


def stale_modules(
    imported: Iterable[str], pinned: Collection[str], extensions: Collection[str]
) -> list[str]:
    """Project modules a reload must forget so the next import reads the edited files.

    Pinned modules are the ones the bot itself imported at startup (error classes,
    stores). Replacing them would leave the running bot holding the old copies.
    """
    return sorted(
        name
        for name in imported
        if "." in name
        and name.split(".")[0] in RELOADABLE_ROOTS
        and name not in pinned
        and name not in extensions
    )


def purge_stale_modules(
    pinned: Collection[str],
    extensions: Collection[str],
    modules: MutableMapping[str, object] | None = None,
) -> dict[str, object]:
    modules = sys.modules if modules is None else modules
    removed = {name: modules.pop(name) for name in stale_modules(list(modules), pinned, extensions)}
    importlib.invalidate_caches()
    return removed


def restore_unused_modules(
    removed: Mapping[str, object], modules: MutableMapping[str, object] | None = None
) -> None:
    """Put back purged modules the reload did not import again, since other cogs still use them."""
    modules = sys.modules if modules is None else modules
    for name, module in removed.items():
        modules.setdefault(name, module)


def command_signature(bot: commands.Bot) -> list[dict]:
    commands_ = bot.tree.get_commands()
    return sorted((command.to_dict(bot.tree) for command in commands_), key=lambda c: c["name"])


@dataclass(frozen=True)
class ReloadResult:
    extension: str
    verb: str
    error: str | None = None


@dataclass(frozen=True)
class ReloadReport:
    results: tuple[ReloadResult, ...]
    synced: int | None = None
    sync_failed: bool = False


def describe_failure(error: commands.ExtensionError) -> str:
    cause = getattr(error, "original", None) or error.__cause__ or error
    return f"{type(cause).__name__}: {cause}"[:MAX_FAILURE_LENGTH]


async def _run_all(
    action: Callable[[str], Awaitable[None]], extensions: Iterable[str], verb: str
) -> list[ReloadResult]:
    results = []
    for extension in extensions:
        try:
            await action(extension)
        except commands.ExtensionError as error:
            log.exception("Could not %s %s", verb, extension)
            results.append(ReloadResult(extension, verb, describe_failure(error)))
        else:
            results.append(ReloadResult(extension, verb))
    return results


async def _sync_if_changed(bot: commands.Bot, changed: bool) -> tuple[int | None, bool]:
    if not changed:
        return None, False
    try:
        return len(await bot.tree.sync()), False
    except discord.HTTPException:
        log.exception("Slash command sync failed after a reload")
        return None, True


async def reload_extensions(
    bot: commands.Bot, plan: ReloadPlan, pinned_modules: Collection[str]
) -> ReloadReport:
    before = command_signature(bot)
    removed = purge_stale_modules(pinned_modules, bot.extensions)
    try:
        results = [
            *await _run_all(bot.unload_extension, plan.unload, "unload"),
            *await _run_all(bot.reload_extension, plan.reload, "reload"),
            *await _run_all(bot.load_extension, plan.load, "load"),
        ]
    finally:
        restore_unused_modules(removed)
    synced, sync_failed = await _sync_if_changed(bot, command_signature(bot) != before)
    return ReloadReport(tuple(results), synced, sync_failed)


def format_report(report: ReloadReport) -> str:
    lines = [_format_result(result) for result in report.results]
    if report.synced is not None:
        lines.append(f"Synced {report.synced} slash commands.")
    if report.sync_failed:
        lines.append("Slash command sync failed. Check the log.")
    return "\n".join(lines or ["Nothing to reload."])[:MAX_REPORT_LENGTH]


def _format_result(result: ReloadResult) -> str:
    name = f"`{result.extension}`"
    if result.error is None:
        return f"{result.verb.capitalize()}ed {name}."
    kept = " The previous version is still running." if result.verb == "reload" else ""
    return f"Could not {result.verb} {name}: {result.error}.{kept}"
