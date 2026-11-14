import subprocess
from pathlib import Path

GIT_TIMEOUT_SECONDS = 5


def _git(repo: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def current_commit(repo: Path) -> str | None:
    return _git(repo, "rev-parse", "--short", "HEAD") or None


def has_uncommitted_changes(repo: Path) -> bool | None:
    changes = _git(repo, "status", "--porcelain")
    return None if changes is None else bool(changes)
