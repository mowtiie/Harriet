from datetime import timedelta

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
MAX_PARTS = 3


def format_elapsed(duration: timedelta) -> str:
    days, remainder = divmod(int(duration.total_seconds()), SECONDS_PER_DAY)
    hours, remainder = divmod(remainder, SECONDS_PER_HOUR)
    minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)
    amounts = ((days, "d"), (hours, "h"), (minutes, "m"), (seconds, "s"))
    parts = [f"{value}{unit}" for value, unit in amounts if value]
    return " ".join(parts[:MAX_PARTS]) or "0s"
