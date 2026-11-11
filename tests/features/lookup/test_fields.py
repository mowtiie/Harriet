"""Tests for member, server and role detail formatting."""

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

import discord

from features.lookup.fields import (
    MAX_ROLES_SHOWN,
    NONE_LABEL,
    avatar_urls,
    format_roles,
    key_permissions,
    role_fields,
    server_fields,
    user_fields,
)

MOMENT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_role(name: str, default: bool = False, **overrides: object) -> SimpleNamespace:
    values = {
        "id": 7,
        "name": name,
        "mention": f"<@&{name}>",
        "created_at": MOMENT,
        "colour": discord.Colour(0),
        "position": 3,
        "members": [1, 2],
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "is_default": lambda: default,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_member(**overrides: object) -> SimpleNamespace:
    everyone, admin, mod = make_role("everyone", True), make_role("admin"), make_role("mod")
    values = {
        "id": 5,
        "created_at": MOMENT,
        "joined_at": MOMENT,
        "top_role": admin,
        "roles": [everyone, mod, admin],
        "premium_since": None,
        "timed_out_until": None,
        "bot": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FormatRolesTests(unittest.TestCase):
    def test_no_roles(self) -> None:
        self.assertEqual(format_roles([]), NONE_LABEL)

    def test_lists_mentions(self) -> None:
        self.assertEqual(format_roles([make_role("a"), make_role("b")]), "<@&a>, <@&b>")

    def test_truncates_long_lists(self) -> None:
        roles = [make_role(str(i)) for i in range(MAX_ROLES_SHOWN + 2)]
        self.assertTrue(format_roles(roles).endswith("and 2 more"))


class KeyPermissionsTests(unittest.TestCase):
    def test_administrator_hides_everything_else(self) -> None:
        self.assertEqual(key_permissions(discord.Permissions.all()), ["Administrator"])

    def test_lists_only_notable_permissions(self) -> None:
        permissions = discord.Permissions(ban_members=True, send_messages=True)
        self.assertEqual(key_permissions(permissions), ["Ban Members"])

    def test_no_notable_permissions(self) -> None:
        self.assertEqual(key_permissions(discord.Permissions(send_messages=True)), [])


class UserFieldsTests(unittest.TestCase):
    def test_lists_roles_highest_first_without_everyone(self) -> None:
        fields = dict(user_fields(make_member()))
        self.assertEqual(fields["Roles (2)"], "<@&admin>, <@&mod>")
        self.assertEqual(fields["Top role"], "<@&admin>")
        self.assertEqual(fields["ID"], "`5`")

    def test_optional_fields_only_appear_when_relevant(self) -> None:
        plain = [label for label, _ in user_fields(make_member())]
        self.assertNotIn("Bot", plain)
        self.assertNotIn("Boosting since", plain)
        self.assertNotIn("Timed out until", plain)

        busy = [
            label
            for label, _ in user_fields(
                make_member(bot=True, premium_since=MOMENT, timed_out_until=MOMENT)
            )
        ]
        self.assertEqual(busy[-3:], ["Boosting since", "Timed out until", "Bot"])

    def test_unknown_join_date(self) -> None:
        self.assertEqual(dict(user_fields(make_member(joined_at=None)))["Joined"], "Unknown")


class ServerAndRoleFieldsTests(unittest.TestCase):
    def test_server_fields(self) -> None:
        guild = SimpleNamespace(
            owner_id=1,
            id=2,
            created_at=MOMENT,
            member_count=30,
            text_channels=[1, 2, 3],
            voice_channels=[1],
            categories=[1, 2],
            roles=[1, 2, 3, 4],
            emojis=[1],
            premium_tier=2,
            premium_subscription_count=9,
            verification_level=discord.VerificationLevel.highest,
        )
        fields = dict(server_fields(guild))
        self.assertEqual(fields["Owner"], "<@1>")
        self.assertEqual(fields["Channels"], "3 text, 1 voice, 2 categories")
        self.assertEqual(fields["Roles"], "3")
        self.assertEqual(fields["Boosts"], "Level 2 (9 boosts)")
        self.assertEqual(fields["Verification"], "Highest")

    def test_role_fields(self) -> None:
        role = make_role(
            "mod",
            colour=discord.Colour(0xFF0000),
            hoist=True,
            permissions=discord.Permissions(kick_members=True),
        )
        fields = dict(role_fields(role))
        self.assertEqual(fields["Color"], "#ff0000")
        self.assertEqual(fields["Members"], "2")
        self.assertEqual(fields["Displayed separately"], "Yes")
        self.assertEqual(fields["Key permissions"], "Kick Members")

    def test_role_without_color_or_permissions(self) -> None:
        fields = dict(role_fields(make_role("plain")))
        self.assertEqual(fields["Color"], "Default")
        self.assertEqual(fields["Key permissions"], NONE_LABEL)


class FakeAsset:
    def __init__(self, url: str) -> None:
        self._url = url

    def with_size(self, size: int) -> "FakeAsset":
        return FakeAsset(f"{self._url}?size={size}")

    @property
    def url(self) -> str:
        return self._url


class AvatarUrlsTests(unittest.TestCase):
    def test_global_avatar_only(self) -> None:
        member = SimpleNamespace(
            avatar=FakeAsset("global"), default_avatar=FakeAsset("default"), guild_avatar=None
        )
        self.assertEqual(avatar_urls(member), [("Avatar", "global?size=1024")])

    def test_falls_back_to_default_avatar(self) -> None:
        member = SimpleNamespace(avatar=None, default_avatar=FakeAsset("default"), guild_avatar=None)
        self.assertEqual(avatar_urls(member), [("Avatar", "default?size=1024")])

    def test_server_avatar_comes_first(self) -> None:
        member = SimpleNamespace(
            avatar=FakeAsset("global"),
            default_avatar=FakeAsset("default"),
            guild_avatar=FakeAsset("server"),
        )
        self.assertEqual(
            avatar_urls(member),
            [("Server avatar", "server?size=1024"), ("Global avatar", "global?size=1024")],
        )


if __name__ == "__main__":
    unittest.main()
