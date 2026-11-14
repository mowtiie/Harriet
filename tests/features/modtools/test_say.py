"""Tests for the helpers behind /say."""

import unittest
from types import SimpleNamespace

import discord

from core.errors import UserError
from features.modtools.say import (
    MAX_LOGGED_LENGTH,
    MAX_MESSAGE_LENGTH,
    build_say_log_view,
    ensure_can_say,
    mention_rules,
    prepare_message,
    quote_for_log,
)


class PrepareMessageTests(unittest.TestCase):
    def test_surrounding_space_is_trimmed(self) -> None:
        self.assertEqual(prepare_message("  hello there \n"), "hello there")

    def test_a_typed_backslash_n_becomes_a_line_break(self) -> None:
        self.assertEqual(prepare_message("line one\\nline two"), "line one\nline two")

    def test_real_line_breaks_are_kept(self) -> None:
        self.assertEqual(prepare_message("a\nb"), "a\nb")

    def test_nothing_to_say_is_refused(self) -> None:
        for text in ("", "   ", "\\n", "\\n\\n  "):
            with self.subTest(text=text), self.assertRaises(ValueError):
                prepare_message(text)

    def test_the_length_limit_is_discords(self) -> None:
        self.assertEqual(len(prepare_message("x" * MAX_MESSAGE_LENGTH)), MAX_MESSAGE_LENGTH)
        with self.assertRaises(ValueError) as caught:
            prepare_message("x" * (MAX_MESSAGE_LENGTH + 1))
        self.assertIn("2001", str(caught.exception))


class MentionRulesTests(unittest.TestCase):
    def test_without_the_permission_nothing_mass_pings(self) -> None:
        rules = mention_rules(can_mention_everyone=False)
        self.assertFalse(rules.everyone)
        self.assertFalse(rules.roles)

    def test_with_the_permission_everyone_and_roles_can_be_pinged(self) -> None:
        rules = mention_rules(can_mention_everyone=True)
        self.assertTrue(rules.everyone)
        self.assertTrue(rules.roles)

    def test_individual_members_can_always_be_mentioned_but_nothing_is_replied_to(self) -> None:
        for allowed in (True, False):
            rules = mention_rules(allowed)
            self.assertTrue(rules.users)
            self.assertFalse(rules.replied_user)


class EnsureCanSayTests(unittest.TestCase):
    ALLOWED = discord.Permissions(view_channel=True, send_messages=True)
    NO_SEND = discord.Permissions(view_channel=True, send_messages=False)
    NO_VIEW = discord.Permissions(view_channel=False, send_messages=True)

    def channel_for(self, member: discord.Permissions, bot: discord.Permissions) -> SimpleNamespace:
        permissions = {"member": member, "bot": bot}
        return SimpleNamespace(permissions_for=permissions.get, mention="<#9>")

    def test_when_both_can_post_it_is_allowed(self) -> None:
        channel = self.channel_for(self.ALLOWED, self.ALLOWED)
        ensure_can_say(channel, "member", "bot")

    def test_a_member_who_cannot_post_there_cannot_use_me_to_do_it(self) -> None:
        for permissions in (self.NO_SEND, self.NO_VIEW):
            with self.subTest(permissions=permissions), self.assertRaises(UserError) as caught:
                ensure_can_say(self.channel_for(permissions, self.ALLOWED), "member", "bot")
            self.assertEqual(str(caught.exception), "You can't send messages in <#9>.")

    def test_a_channel_i_cannot_post_in_is_explained(self) -> None:
        for permissions in (self.NO_SEND, self.NO_VIEW):
            with self.subTest(permissions=permissions), self.assertRaises(UserError) as caught:
                ensure_can_say(self.channel_for(self.ALLOWED, permissions), "member", "bot")
            self.assertEqual(str(caught.exception), "I can't send messages in <#9>.")


class QuoteForLogTests(unittest.TestCase):
    def test_every_line_is_quoted(self) -> None:
        self.assertEqual(quote_for_log("one\ntwo"), "> one\n> two")

    def test_long_text_is_cut_with_an_ellipsis(self) -> None:
        quoted = quote_for_log("x" * 2000)
        self.assertEqual(len(quoted), len("> ") + MAX_LOGGED_LENGTH)
        self.assertTrue(quoted.endswith("…"))

    def test_text_at_the_limit_is_left_alone(self) -> None:
        text = "x" * MAX_LOGGED_LENGTH
        self.assertEqual(quote_for_log(text), f"> {text}")


def texts_in(view: discord.ui.LayoutView) -> list[str]:
    return [item.content for item in view.walk_children() if hasattr(item, "content")]


class BuildSayLogViewTests(unittest.TestCase):
    def make_view(self, content: str = "Server restarts at 8pm") -> discord.ui.LayoutView:
        moderator = SimpleNamespace(mention="<@1>")
        channel = SimpleNamespace(mention="<#9>")
        sent = SimpleNamespace(content=content, jump_url="https://discord.com/channels/1/9/77")
        return build_say_log_view(moderator, channel, sent)

    def test_the_log_says_who_said_what_and_where(self) -> None:
        text = "\n".join(texts_in(self.make_view()))
        self.assertIn("Said as the bot", text)
        self.assertIn("**Moderator** · <@1>", text)
        self.assertIn("<#9>", text)
        self.assertIn("(https://discord.com/channels/1/9/77)", text)
        self.assertIn("> Server restarts at 8pm", text)

    def test_what_was_said_cannot_break_out_of_the_quote(self) -> None:
        text = "\n".join(texts_in(self.make_view("first\n**Moderator** · <@999>")))
        self.assertIn("> **Moderator** · <@999>", text)

    def test_the_log_view_never_times_out(self) -> None:
        self.assertIsNone(self.make_view().timeout)


if __name__ == "__main__":
    unittest.main()
