import re
from datetime import timedelta

from time_format import SECONDS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MINUTE

DAYS_PER_WEEK = 7
MAX_TIMEOUT_DAYS = 28
UNIT_SECONDS = {
    "w": DAYS_PER_WEEK * SECONDS_PER_DAY,
    "d": SECONDS_PER_DAY,
    "h": SECONDS_PER_HOUR,
    "m": SECONDS_PER_MINUTE,
    "s": 1,
}
MAX_TIMEOUT = timedelta(days=MAX_TIMEOUT_DAYS)
DURATION_HINT = "Use a duration like `30m`, `2h`, `3d` or `1h30m`."

_PART = re.compile(r"(\d+)([wdhms])")


def parse_duration(text: str, maximum: timedelta = MAX_TIMEOUT) -> timedelta:
    cleaned = "".join(text.lower().split())
    parts = _PART.findall(cleaned)
    if not parts or "".join(f"{amount}{unit}" for amount, unit in parts) != cleaned:
        raise ValueError(f"Couldn't read `{text}` as a duration. {DURATION_HINT}")

    total = timedelta(seconds=sum(int(amount) * UNIT_SECONDS[unit] for amount, unit in parts))
    if total <= timedelta():
        raise ValueError(f"The duration must be longer than zero. {DURATION_HINT}")
    if total > maximum:
        raise ValueError(f"The duration can't be longer than {maximum.days} days.")
    return total
