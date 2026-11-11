"""Tests for the shared profile and avatar cards."""

import unittest

from views.profile_view import build_avatar_view, build_profile_view, format_fields

SECTION = 9
TEXT_DISPLAY = 10


class FormatFieldsTests(unittest.TestCase):
    def test_one_bold_label_and_value_per_line(self) -> None:
        self.assertEqual(
            format_fields([("ID", "`1`"), ("Level", "4")]), "**ID** · `1`\n**Level** · 4"
        )

    def test_no_fields(self) -> None:
        self.assertEqual(format_fields([]), "")


class BuildProfileViewTests(unittest.TestCase):
    FIELDS = [("ID", "`1`")]

    def first_component_type(self, view: object) -> int:
        return view.to_components()[0]["components"][0]["type"]

    def test_thumbnail_turns_the_header_into_a_section(self) -> None:
        view = build_profile_view("Name", "Sub", self.FIELDS, "https://example.com/a.png")
        self.assertEqual(self.first_component_type(view), SECTION)

    def test_without_thumbnail_the_header_is_plain_text(self) -> None:
        view = build_profile_view("Name", "Sub", self.FIELDS)
        self.assertEqual(self.first_component_type(view), TEXT_DISPLAY)


class BuildAvatarViewTests(unittest.TestCase):
    def gallery_items(self, urls: list[tuple[str, str]]) -> list[dict]:
        container = build_avatar_view("Name", urls).to_components()[0]
        return container["components"][1]["items"]

    def test_one_gallery_item_per_avatar(self) -> None:
        urls = [
            ("Server avatar", "https://example.com/s.png"),
            ("Global avatar", "https://example.com/g.png"),
        ]
        self.assertEqual(len(self.gallery_items(urls)), 2)

    def test_single_avatar(self) -> None:
        self.assertEqual(len(self.gallery_items([("Avatar", "https://example.com/a.png")])), 1)


if __name__ == "__main__":
    unittest.main()
