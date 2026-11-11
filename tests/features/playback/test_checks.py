"""Tests for voice state validation."""

import unittest

from features.playback.checks import (
    JOIN_FIRST_MESSAGE,
    NOT_CONNECTED_MESSAGE,
    SAME_CHANNEL_MESSAGE,
    voice_state_error,
)


class VoiceStateErrorTests(unittest.TestCase):
    def test_user_must_be_in_a_voice_channel(self) -> None:
        self.assertEqual(voice_state_error(None, None, require_bot=False), JOIN_FIRST_MESSAGE)
        self.assertEqual(voice_state_error(None, 5, require_bot=True), JOIN_FIRST_MESSAGE)

    def test_bot_not_connected_is_fine_unless_required(self) -> None:
        self.assertIsNone(voice_state_error(1, None, require_bot=False))
        self.assertEqual(voice_state_error(1, None, require_bot=True), NOT_CONNECTED_MESSAGE)

    def test_user_must_share_the_bot_channel(self) -> None:
        self.assertEqual(voice_state_error(1, 2, require_bot=False), SAME_CHANNEL_MESSAGE)
        self.assertIsNone(voice_state_error(1, 1, require_bot=True))


if __name__ == "__main__":
    unittest.main()
