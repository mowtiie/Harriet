import re
from datetime import datetime, timedelta, timezone, tzinfo
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

UTC = timezone.utc
UTC_NAMES = frozenset({"utc", "gmt", "z"})
MAX_OFFSET_HOURS = 14
MINUTES_PER_HOUR = 60
ZONE_HINT = "Use a city like `London`, a name like `Europe/London`, or an offset like `UTC+2`."

# Abbreviations people actually type, mapped to a place so daylight saving works.
ALIASES = {
    "est": "America/New_York",
    "edt": "America/New_York",
    "et": "America/New_York",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "ct": "America/Chicago",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "mt": "America/Denver",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "bst": "Europe/London",
    "cet": "Europe/Paris",
    "cest": "Europe/Paris",
    "eet": "Europe/Athens",
    "eest": "Europe/Athens",
    "jst": "Asia/Tokyo",
    "kst": "Asia/Seoul",
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
}

_OFFSET = re.compile(r"(?:utc|gmt)?([+-])(\d{1,2})(?::?(\d{2}))?")


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("_", " ").replace("-", " ").split())


@lru_cache(maxsize=1)
def _zone_index() -> dict[str, str]:
    """Maps full names and unambiguous city names, like `new york`, to zone keys."""
    index: dict[str, str] = {}
    cities: dict[str, str | None] = {}
    for key in sorted(available_timezones()):
        index[_normalize(key.replace("/", " / "))] = key
        index[key.lower()] = key
        if "/" in key and not key.startswith("Etc/"):
            city = _normalize(key.rsplit("/", 1)[1])
            cities[city] = None if cities.get(city, key) != key else key
    index.update({city: key for city, key in cities.items() if key and city not in index})
    return index


class TimezoneDataError(ValueError):
    """The place is real but this system has no timezone data for it."""


def _load_zone(key: str) -> ZoneInfo:
    try:
        return ZoneInfo(key)
    except ZoneInfoNotFoundError as error:
        raise TimezoneDataError(
            f"Timezone data for `{key}` isn't installed on this system."
        ) from error


def _fixed_offset(match: re.Match[str]) -> timezone:
    sign, hours, minutes = match.group(1), int(match.group(2)), int(match.group(3) or 0)
    if hours > MAX_OFFSET_HOURS or minutes >= MINUTES_PER_HOUR:
        raise ValueError(f"`UTC{sign}{hours}` isn't a real timezone offset. {ZONE_HINT}")
    delta = timedelta(hours=hours, minutes=minutes)
    name = f"UTC{sign}{hours:02d}:{minutes:02d}"
    return timezone(delta if sign == "+" else -delta, name)


def parse_timezone(text: str) -> tzinfo:
    cleaned = " ".join(text.lower().split())
    if cleaned in UTC_NAMES:
        return UTC
    if cleaned in ALIASES:
        return _load_zone(ALIASES[cleaned])
    offset = _OFFSET.fullmatch(cleaned.replace(" ", ""))
    if offset:
        return _fixed_offset(offset)
    key = _zone_index().get(cleaned) or _zone_index().get(_normalize(cleaned))
    if key:
        return _load_zone(key)
    raise ValueError(f"Couldn't find the timezone `{text.strip()}`. {ZONE_HINT}")


def split_timezone(text: str) -> tuple[tzinfo, str]:
    """Take a trailing timezone off the text, like `8pm New York`, or fall back to UTC."""
    tokens = text.split()
    for size in (2, 1):
        if len(tokens) <= size:
            continue
        try:
            zone = parse_timezone(" ".join(tokens[-size:]))
        except TimezoneDataError:
            raise
        except ValueError:
            continue
        return zone, " ".join(tokens[:-size])
    return UTC, text


def describe_zone(zone: tzinfo | None) -> str:
    return getattr(zone, "key", None) or str(zone)


def format_utc_offset(moment: datetime) -> str:
    total_minutes = int((moment.utcoffset() or timedelta()).total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), MINUTES_PER_HOUR)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"
