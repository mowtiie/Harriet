from dataclasses import dataclass
from datetime import timedelta

from core.time_format import format_elapsed

BYTES_PER_UNIT = 1024
SIZE_UNITS = ("B", "KB", "MB", "GB")
MILLISECONDS_PER_SECOND = 1000


def format_size(size: int) -> str:
    value = float(size)
    for unit in SIZE_UNITS[:-1]:
        if value < BYTES_PER_UNIT:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= BYTES_PER_UNIT
    return f"{value:.1f} {SIZE_UNITS[-1]}"


@dataclass(frozen=True)
class StatusInfo:
    uptime: timedelta
    latency_ms: int
    guild_count: int
    voice_connections: int
    active_games: int
    commit: str | None
    started_commit: str | None
    has_uncommitted_changes: bool | None
    loaded_cogs: int
    unloaded_cogs: tuple[str, ...]
    command_count: int
    database_bytes: int | None
    error_count: int
    last_error: str | None


def _commit_line(info: StatusInfo) -> str:
    if info.commit is None:
        return "Commit **unknown** (git isn't available)"
    line = f"Commit `{info.commit}`"
    if info.started_commit and info.started_commit != info.commit:
        line += f" (started on `{info.started_commit}`)"
    if info.has_uncommitted_changes:
        line += " · uncommitted changes"
    return line


def _cogs_line(info: StatusInfo) -> str:
    line = f"Cogs **{info.loaded_cogs} loaded**"
    if info.unloaded_cogs:
        line += " · not loaded: " + ", ".join(f"`{name}`" for name in info.unloaded_cogs)
    return f"{line} · Slash commands **{info.command_count}**"


def _database_line(info: StatusInfo) -> str:
    if info.database_bytes is None:
        return "Database **no file yet**"
    return f"Database **{format_size(info.database_bytes)}**"


def _errors_line(info: StatusInfo) -> str:
    line = f"Errors since start **{info.error_count}**"
    return f"{line}\n-# Last: `{info.last_error}`" if info.last_error else line


def format_status(info: StatusInfo) -> str:
    return "\n".join(
        [
            "**Status**",
            f"Uptime **{format_elapsed(info.uptime)}** · Latency **{info.latency_ms} ms**"
            f" · Servers **{info.guild_count}**",
            f"Games in progress **{info.active_games}**"
            f" · Voice connections **{info.voice_connections}**",
            _commit_line(info),
            _cogs_line(info),
            _database_line(info),
            _errors_line(info),
        ]
    )
