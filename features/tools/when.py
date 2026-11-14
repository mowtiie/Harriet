import re
from datetime import date, datetime, time, timedelta, timezone

from core.durations import parse_duration
from features.tools.timezones import describe_zone, format_utc_offset

MAX_AHEAD = timedelta(days=5 * 365)
DAYS_PER_WEEK = 7
NOON_HOUR = 12
WEEKDAYS = {
    name: number
    for number, names in enumerate(
        (
            ("monday", "mon"),
            ("tuesday", "tue", "tues"),
            ("wednesday", "wed"),
            ("thursday", "thu", "thur", "thurs"),
            ("friday", "fri"),
            ("saturday", "sat"),
            ("sunday", "sun"),
        )
    )
    for name in names
}
WHEN_HINT = (
    "Try `tomorrow 8pm`, `friday 18:30 London`, `2026-12-25 09:00 UTC+2` or `in 2h`."
)

_CLOCK = re.compile(r"(\d{1,2})(?::(\d{2}))?(am|pm)?")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_NAMED_TIMES = {"noon": time(12), "midnight": time(0)}


def _is_day(token: str) -> bool:
    return token in ("today", "tomorrow") or token in WEEKDAYS or bool(_ISO_DATE.fullmatch(token))


def _parse_clock(text: str, shown: str) -> time:
    if text in _NAMED_TIMES:
        return _NAMED_TIMES[text]
    match = _CLOCK.fullmatch(text)
    if match is None:
        raise ValueError(
            f"Couldn't read `{shown}` as a time of day. "
            f"If part of it is a timezone, check its spelling. {WHEN_HINT}"
        )
    hour, minute, meridiem = int(match.group(1)), int(match.group(2) or 0), match.group(3)
    if meridiem:
        if not 1 <= hour <= NOON_HOUR:
            raise ValueError(f"`{text}` isn't a real time. Use 1 to 12 with am or pm.")
        hour = hour % NOON_HOUR + (NOON_HOUR if meridiem == "pm" else 0)
    if hour > 23 or minute > 59:
        raise ValueError(f"`{text}` isn't a real time of day.")
    return time(hour, minute)


def _pick_date(day: str | None, clock: time, now: datetime) -> date:
    today = now.date()
    if day == "today":
        return today
    if day == "tomorrow":
        return today + timedelta(days=1)
    if day is not None and _ISO_DATE.fullmatch(day):
        try:
            return date.fromisoformat(day)
        except ValueError as error:
            raise ValueError(f"`{day}` isn't a real date.") from error
    already_passed = datetime.combine(today, clock, tzinfo=now.tzinfo) <= now
    if day is None:
        return today + timedelta(days=1) if already_passed else today
    days_ahead = (WEEKDAYS[day] - today.weekday()) % DAYS_PER_WEEK
    if days_ahead == 0 and already_passed:
        days_ahead = DAYS_PER_WEEK
    return today + timedelta(days=days_ahead)


def _find_day(tokens: list[str]) -> tuple[str | None, slice]:
    """The day word, if there is one at either end, and which words are left for the time."""
    if tokens and _is_day(tokens[0]):
        return tokens[0], slice(1, None)
    if tokens and _is_day(tokens[-1]):
        return tokens[-1], slice(None, -1)
    return None, slice(None)


def parse_when(text: str, now: datetime) -> datetime:
    """Read `tomorrow 8pm`, `friday 18:30`, `2026-12-25 09:00`, `8pm` or `in 2h`."""
    words = text.split()
    tokens = [word.lower() for word in words]
    if tokens == ["now"]:
        return now
    if len(tokens) > 1 and tokens[0] == "in":
        delta = parse_duration(" ".join(tokens[1:]), MAX_AHEAD)
        return (now.astimezone(timezone.utc) + delta).astimezone(now.tzinfo)

    day, remaining = _find_day(tokens)
    rest = tokens[remaining]
    if not rest:
        hint = f" Add a time, like `{day} 8pm`." if day else f" {WHEN_HINT}"
        raise ValueError(f"Couldn't read `{text.strip()}` as a time.{hint}")
    clock = _parse_clock("".join(rest), shown=" ".join(words[remaining]))
    return datetime.combine(_pick_date(day, clock, now), clock, tzinfo=now.tzinfo)


def format_time_reply(moment: datetime) -> str:
    stamp = int(moment.timestamp())
    full, short, relative = (f"<t:{stamp}:{style}>" for style in "FtR")
    zone = f"{describe_zone(moment.tzinfo)} ({format_utc_offset(moment)})"
    return "\n".join(
        [
            f"**{full}** ({relative})",
            f"-# Read as {moment:%a %d %b %Y, %H:%M} in {zone}.",
            "Copy one of these, and everyone sees it in their own timezone:",
            f"`{full}` · `{short}` · `{relative}`",
        ]
    )
