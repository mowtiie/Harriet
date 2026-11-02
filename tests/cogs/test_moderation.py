"""Tests for moderation helpers."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from cogs.moderation import (
    CONFIRMATION_DELETE_DELAY_SECONDS,
    clear_summary,
    deleted_count,
    purge_limit,
    send_confirmation,
)


class PurgeMathTests(unittest.TestCase):
    def test_prefix_invocation_gets_extra_slot(self) -> None:
        self.assertEqual(purge_limit(5, invoked_by_message=True), 6)
        self.assertEqual(purge_limit(5, invoked_by_message=False), 5)

    def test_deleted_count_excludes_command_message(self) -> None:
        self.assertEqual(deleted_count(6, invoked_by_message=True), 5)
        self.assertEqual(deleted_count(5, invoked_by_message=False), 5)

    def test_deleted_count_never_negative(self) -> None:
        self.assertEqual(deleted_count(0, invoked_by_message=True), 0)

    def test_summary_text(self) -> None:
        self.assertEqual(clear_summary(3), "Deleted 3 message(s).")


class SendConfirmationTests(unittest.IsolatedAsyncioTestCase):
    async def test_slash_reply_is_ephemeral(self) -> None:
        ctx = MagicMock(interaction=object())
        ctx.send = AsyncMock()
        await send_confirmation(ctx, "done")
        ctx.send.assert_awaited_once_with("done", ephemeral=True)

    async def test_prefix_reply_deletes_itself(self) -> None:
        sent = MagicMock()
        sent.delete = AsyncMock()
        ctx = MagicMock(interaction=None)
        ctx.send = AsyncMock(return_value=sent)
        await send_confirmation(ctx, "done")
        ctx.send.assert_awaited_once_with("done")
        sent.delete.assert_awaited_once_with(delay=CONFIRMATION_DELETE_DELAY_SECONDS)


if __name__ == "__main__":
    unittest.main()
