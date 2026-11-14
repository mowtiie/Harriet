"""Tests for the /time command: timezones, reading times, and the reply."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from features.tools.timezones import (
    ALIASES,
    UTC,
    TimezoneDataError,
    describe_zone,
    format_utc_offset,
    parse_timezone,
    split_timezone,
)
from features.tools.when import format_time_reply, parse_when

PLUS_ONE = timezone(timedelta(hours=1), "UTC+01:00")
# Saturday 14 November 2026, 15:00 in a fixed UTC+1 zone, so no timezone data is needed.
NOW = datetime(2026, 11, 14, 15, 0, tzinfo=PLUS_ONE)


def read(text: str, now: datetime = NOW) -> datetime:
    return parse_when(text, now)


def at(day: int, hour: int, minute: int = 0, month: int = 11) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=PLUS_ONE)


class ParseWhenClockTests(unittest.TestCase):
    def test_a_bare_time_later_today_means_today(self) -> None:
        self.assertEqual(read("8pm"), at(14, 20))

    def test_a_bare_time_that_has_passed_means_tomorrow(self) -> None:
        self.assertEqual(read("2pm"), at(15, 14))
        self.assertEqual(read("3pm"), at(15, 15))

    def test_the_different_ways_to_write_a_time(self) -> None:
        self.assertEqual(read("8:30pm"), at(14, 20, 30))
        self.assertEqual(read("8 pm"), at(14, 20))
        self.assertEqual(read("20:45"), at(14, 20, 45))
        self.assertEqual(read("noon tomorrow"), at(15, 12))
        self.assertEqual(read("midnight"), at(15, 0))

    def test_twelve_am_and_pm_are_midnight_and_noon(self) -> None:
        self.assertEqual(read("tomorrow 12am"), at(15, 0))
        self.assertEqual(read("tomorrow 12pm"), at(15, 12))
        self.assertEqual(read("tomorrow 12:30 am"), at(15, 0, 30))

    def test_the_error_shows_what_was_typed_and_hints_at_a_misspelled_zone(self) -> None:
        zone, text = split_timezone("tomorrow 8pm Lndon")
        with self.assertRaises(ValueError) as caught:
            read(text)
        message = str(caught.exception)
        self.assertIn("`8pm Lndon`", message)
        self.assertNotIn("8pmlndon", message)
        self.assertIn("check its spelling", message)

    def test_invalid_times_are_refused(self) -> None:
        for text in ("13pm", "0am", "25:00", "8:75", "banana", "", "in", "tomorrow"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read(text)


class ParseWhenDayTests(unittest.TestCase):
    def test_today_and_tomorrow(self) -> None:
        self.assertEqual(read("today 8am"), at(14, 8))
        self.assertEqual(read("tomorrow 8pm"), at(15, 20))

    def test_a_weekday_is_the_next_one_coming(self) -> None:
        self.assertEqual(read("sunday 9am"), at(15, 9))
        self.assertEqual(read("friday 18:30"), at(20, 18, 30))
        self.assertEqual(read("fri 18:30"), at(20, 18, 30))

    def test_todays_weekday_means_today_unless_the_time_has_passed(self) -> None:
        self.assertEqual(read("saturday 8pm"), at(14, 20))
        self.assertEqual(read("saturday 8am"), at(21, 8))

    def test_the_day_can_come_after_the_time(self) -> None:
        self.assertEqual(read("8pm tomorrow"), at(15, 20))

    def test_an_exact_date(self) -> None:
        self.assertEqual(read("2026-12-25 09:00"), at(25, 9, month=12))
        self.assertEqual(read("2020-01-01 00:00"), datetime(2020, 1, 1, tzinfo=PLUS_ONE))

    def test_a_date_that_does_not_exist_is_refused(self) -> None:
        with self.assertRaises(ValueError) as caught:
            read("2026-02-30 09:00")
        self.assertIn("isn't a real date", str(caught.exception))

    def test_a_day_without_a_time_asks_for_one(self) -> None:
        with self.assertRaises(ValueError) as caught:
            read("tomorrow")
        self.assertIn("Add a time", str(caught.exception))


class ParseWhenRelativeTests(unittest.TestCase):
    def test_now_is_now(self) -> None:
        self.assertEqual(read("now"), NOW)

    def test_in_a_duration(self) -> None:
        self.assertEqual(read("in 2h30m"), at(14, 17, 30))
        self.assertEqual(read("in 90m"), at(14, 16, 30))
        self.assertEqual(read("in 2d"), at(16, 15))

    def test_the_zone_is_kept(self) -> None:
        self.assertIs(read("in 2h").tzinfo, PLUS_ONE)

    def test_bad_or_far_off_durations_are_refused(self) -> None:
        for text in ("in banana", "in 0m", "in 9999d"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read(text)


class ParseTimezoneTests(unittest.TestCase):
    def test_utc_and_its_aliases_need_no_data(self) -> None:
        for text in ("utc", "UTC", " gmt ", "z"):
            self.assertIs(parse_timezone(text), UTC)

    def test_offsets(self) -> None:
        self.assertEqual(parse_timezone("UTC+2").utcoffset(None), timedelta(hours=2))
        self.assertEqual(parse_timezone("gmt-5").utcoffset(None), timedelta(hours=-5))
        self.assertEqual(parse_timezone("+5:30").utcoffset(None), timedelta(hours=5, minutes=30))
        self.assertEqual(parse_timezone("+0530").utcoffset(None), timedelta(hours=5, minutes=30))
        self.assertEqual(parse_timezone("utc +2").utcoffset(None), timedelta(hours=2))
        self.assertEqual(parse_timezone("-3:30").utcoffset(None), timedelta(hours=-3, minutes=-30))

    def test_offsets_are_named_for_display(self) -> None:
        self.assertEqual(describe_zone(parse_timezone("+5:30")), "UTC+05:30")
        self.assertEqual(describe_zone(parse_timezone("utc-8")), "UTC-08:00")

    def test_impossible_offsets_are_refused(self) -> None:
        for text in ("+15", "UTC+25", "+5:75"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_timezone(text)

    def test_unknown_zones_get_a_helpful_message(self) -> None:
        with self.assertRaises(ValueError) as caught:
            parse_timezone("Narnia")
        self.assertIn("`Narnia`", str(caught.exception))
        self.assertIn("UTC+2", str(caught.exception))

    def test_missing_timezone_data_is_explained(self) -> None:
        with mock.patch(
            "features.tools.timezones.ZoneInfo", side_effect=ZoneInfoNotFoundError("x")
        ):
            with self.assertRaises(ValueError) as caught:
                parse_timezone("est")
        self.assertIn("isn't installed", str(caught.exception))


class SplitTimezoneTests(unittest.TestCase):
    def test_text_without_a_zone_is_left_alone_and_read_as_utc(self) -> None:
        for text in ("friday 18:30", "tomorrow 8pm", "in 2h", "2026-12-25 09:00"):
            with self.subTest(text=text):
                self.assertEqual(split_timezone(text), (UTC, text))

    def test_a_trailing_zone_is_taken_off(self) -> None:
        zone, rest = split_timezone("tomorrow 8pm UTC+2")
        self.assertEqual((zone.utcoffset(None), rest), (timedelta(hours=2), "tomorrow 8pm"))
        zone, rest = split_timezone("friday 18:30 gmt-5")
        self.assertEqual((zone.utcoffset(None), rest), (timedelta(hours=-5), "friday 18:30"))

    def test_a_lone_word_is_never_swallowed_as_a_zone(self) -> None:
        self.assertEqual(split_timezone("utc"), (UTC, "utc"))

    def test_an_unreadable_zone_falls_back_to_utc_and_keeps_the_text(self) -> None:
        self.assertEqual(split_timezone("tomorrow 8pm Narnia"), (UTC, "tomorrow 8pm Narnia"))

    def test_missing_timezone_data_is_reported_not_hidden_as_utc(self) -> None:
        with mock.patch(
            "features.tools.timezones.ZoneInfo", side_effect=ZoneInfoNotFoundError("x")
        ):
            with self.assertRaises(TimezoneDataError) as caught:
                split_timezone("tomorrow 8pm EST")
        self.assertIn("isn't installed", str(caught.exception))


class FormatTests(unittest.TestCase):
    def test_the_reply_has_live_timestamps_and_copyable_codes(self) -> None:
        reply = format_time_reply(at(15, 20))
        stamp = int(at(15, 20).timestamp())
        self.assertIn(f"**<t:{stamp}:F>** (<t:{stamp}:R>)", reply)
        self.assertIn(f"`<t:{stamp}:F>` · `<t:{stamp}:t>` · `<t:{stamp}:R>`", reply)

    def test_the_reply_says_how_the_time_was_read(self) -> None:
        reply = format_time_reply(at(15, 20))
        self.assertIn("Read as Sun 15 Nov 2026, 20:00 in UTC+01:00 (UTC+01:00).", reply)

    def test_the_timestamp_is_the_real_moment_in_utc(self) -> None:
        stamp = int(at(15, 20).timestamp())
        self.assertEqual(datetime.fromtimestamp(stamp, timezone.utc).hour, 19)

    def test_offsets_are_written_with_a_sign_and_minutes(self) -> None:
        self.assertEqual(format_utc_offset(at(15, 20)), "UTC+01:00")
        india = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        self.assertEqual(format_utc_offset(india), "UTC+05:30")
        newfoundland = datetime(2026, 1, 1, tzinfo=timezone(-timedelta(hours=3, minutes=30)))
        self.assertEqual(format_utc_offset(newfoundland), "UTC-03:30")


class RealZoneTests(unittest.TestCase):
    """These look up real places, so they need the `tzdata` package on Windows."""

    def test_names_cities_and_abbreviations_find_the_same_places(self) -> None:
        self.assertEqual(describe_zone(parse_timezone("Europe/London")), "Europe/London")
        self.assertEqual(describe_zone(parse_timezone("europe/london")), "Europe/London")
        self.assertEqual(describe_zone(parse_timezone("London")), "Europe/London")
        self.assertEqual(describe_zone(parse_timezone("new york")), "America/New_York")
        self.assertEqual(describe_zone(parse_timezone("New_York")), "America/New_York")
        self.assertEqual(describe_zone(parse_timezone("Tokyo")), "Asia/Tokyo")
        self.assertEqual(describe_zone(parse_timezone("PST")), "America/Los_Angeles")

    def test_every_abbreviation_points_at_a_real_zone(self) -> None:
        for alias, key in ALIASES.items():
            with self.subTest(alias=alias):
                self.assertEqual(describe_zone(parse_timezone(alias)), key)

    def test_a_two_word_city_is_split_off_the_end(self) -> None:
        zone, rest = split_timezone("tomorrow 8pm New York")
        self.assertEqual((describe_zone(zone), rest), ("America/New_York", "tomorrow 8pm"))

    def test_daylight_saving_changes_the_offset_through_the_year(self) -> None:
        london = ZoneInfo("Europe/London")
        summer = parse_when("8pm", datetime(2026, 7, 14, 9, 0, tzinfo=london))
        winter = parse_when("8pm", datetime(2026, 11, 14, 9, 0, tzinfo=london))
        self.assertEqual(format_utc_offset(summer), "UTC+01:00")
        self.assertEqual(format_utc_offset(winter), "UTC+00:00")

    def test_a_duration_across_the_clocks_going_back_is_a_real_24_hours(self) -> None:
        london = ZoneInfo("Europe/London")
        before = datetime(2026, 10, 24, 12, 0, tzinfo=london)
        after = parse_when("in 24h", before)
        self.assertEqual(after.hour, 11)
        self.assertEqual(after.astimezone(UTC) - before.astimezone(UTC), timedelta(hours=24))

    def test_a_time_in_another_zone_is_the_right_moment(self) -> None:
        zone, text = split_timezone("2026-11-14 20:00 London")
        moment = parse_when(text, datetime.now(zone))
        self.assertEqual(moment.astimezone(UTC), datetime(2026, 11, 14, 20, 0, tzinfo=UTC))

    def test_the_reply_names_the_place(self) -> None:
        now = datetime(2026, 11, 14, 9, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        moment = parse_when("2026-11-14 20:00", now)
        self.assertIn("in Asia/Tokyo (UTC+09:00)", format_time_reply(moment))


if __name__ == "__main__":
    unittest.main()
