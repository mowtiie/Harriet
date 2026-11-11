"""Tests for info formatting."""

import unittest
from datetime import timedelta

from features.helpinfo.info_view import BotInfo, build_link_buttons


def make_info(repo_url: str = "https://example.com/repo", support_url: str = "") -> BotInfo:
    return BotInfo(
        name="Harriet",
        tagline="Hi",
        avatar_url="https://example.com/a.png",
        version="1.0.0",
        prefix="do ",
        latency_ms=42,
        uptime=timedelta(),
        guild_count=1,
        owner_mention="<@1>",
        python_version="3.12.0",
        discord_version="2.7.0",
        repo_url=repo_url,
        support_url=support_url,
    )


class BuildLinkButtonsTests(unittest.TestCase):
    def test_only_configured_links_become_buttons(self) -> None:
        buttons = build_link_buttons(make_info())
        self.assertEqual([button.label for button in buttons], ["Source code"])

    def test_no_links_gives_no_buttons(self) -> None:
        self.assertEqual(build_link_buttons(make_info(repo_url="")), [])


if __name__ == "__main__":
    unittest.main()
