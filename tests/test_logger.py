"""Tests for the gateway log filter."""

import logging
import unittest

from logger import VoiceEncryptionFilter


def make_record(message: str, level: int = logging.DEBUG) -> logging.LogRecord:
    return logging.LogRecord("discord.gateway", level, __file__, 1, message, None, None)


class VoiceEncryptionFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.filter = VoiceEncryptionFilter()

    def test_lets_encryption_handshake_lines_through(self) -> None:
        for message in (
            "Preparing for DAVE epoch 2",
            "Executing DAVE transition id 4",
            "Set MLS external sender",
            "MLS proposals processed",
            "Voice websocket binary frame received: 12 bytes; seq=1 op=25",
        ):
            with self.subTest(message=message):
                self.assertTrue(self.filter.filter(make_record(message)))

    def test_hides_other_debug_lines_such_as_chat_payloads(self) -> None:
        for message in (
            "For Shard ID None: WebSocket Event: {'t': 'MESSAGE_CREATE', 'd': {'content': 'hi'}}",
            "Voice websocket frame received: {'op': 4, 'd': {'secret_key': [1, 2]}}",
        ):
            with self.subTest(message=message):
                self.assertFalse(self.filter.filter(make_record(message)))

    def test_warnings_and_errors_always_pass(self) -> None:
        self.assertTrue(self.filter.filter(make_record("anything", logging.WARNING)))
        self.assertTrue(self.filter.filter(make_record("anything", logging.ERROR)))


if __name__ == "__main__":
    unittest.main()
