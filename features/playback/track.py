from dataclasses import dataclass

LIVE_LABEL = "Live"
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE


@dataclass(frozen=True)
class Track:
    title: str
    source: str
    is_local: bool
    duration_seconds: int | None
    requested_by: str


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return LIVE_LABEL
    hours, remainder = divmod(seconds, SECONDS_PER_HOUR)
    minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
