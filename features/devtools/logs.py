import os
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LINES = 25
MAX_LINES = 300
MAX_INLINE_CHARS = 1800
MAX_READ_BYTES = 256 * 1024
MAX_SUMMARY_CHARS = 150
ERROR_LEVELS = frozenset({"ERROR", "CRITICAL"})

_ENTRY_START = re.compile(r"\[\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\] \[(\w+)\s*\] (.*)")


@dataclass(frozen=True)
class LogReply:
    message: str
    attachment: str | None = None


def read_log_tail(path: Path, max_bytes: int = MAX_READ_BYTES) -> str:
    """The end of the log file, or an empty string when there isn't one yet."""
    try:
        with path.open("rb") as log_file:
            size = log_file.seek(0, os.SEEK_END)
            log_file.seek(max(0, size - max_bytes))
            data = log_file.read()
    except FileNotFoundError:
        return ""
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    return text.split("\n", 1)[-1] if size > max_bytes else text


def split_entries(text: str) -> list[str]:
    """Group each log record with the traceback lines that follow it."""
    entries: list[list[str]] = []
    for line in text.splitlines():
        if _ENTRY_START.match(line) or not entries:
            entries.append([line])
        else:
            entries[-1].append(line)
    return ["\n".join(entry) for entry in entries]


def error_entries(text: str) -> list[str]:
    found = []
    for entry in split_entries(text):
        match = _ENTRY_START.match(entry)
        if match and match.group(2) in ERROR_LEVELS:
            found.append(entry)
    return found


def summarize_error(entry: str) -> str:
    """One short line for an error entry: its time and message."""
    match = _ENTRY_START.match(entry.splitlines()[0])
    summary = f"{match.group(1)} {match.group(3)}" if match else entry.splitlines()[0]
    summary = summary.replace("`", "'")
    if len(summary) > MAX_SUMMARY_CHARS:
        return summary[: MAX_SUMMARY_CHARS - 1] + "…"
    return summary


def clamp_lines(lines: int) -> int:
    return max(1, min(lines, MAX_LINES))


def build_log_reply(text: str, lines: int, errors_only: bool) -> LogReply:
    source = "\n".join(error_entries(text)) if errors_only else text
    shown = source.splitlines()[-clamp_lines(lines) :]
    if not shown:
        return LogReply("No errors since the last start." if errors_only else "The log is empty.")
    chosen = "\n".join(shown)
    label = f"-# Last {len(shown)} line(s){' of errors' if errors_only else ''}"
    safe = chosen.replace("```", "'''")
    if len(safe) <= MAX_INLINE_CHARS:
        return LogReply(f"{label}\n```\n{safe}\n```")
    return LogReply(f"{label}, too long for a message, so here it is as a file.", chosen)
