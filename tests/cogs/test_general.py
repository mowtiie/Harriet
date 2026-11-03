"""Tests for general helpers."""

import unittest
from urllib.parse import parse_qs, urlparse

from cogs.general import INVITE_PERMISSIONS, build_invite_url


class BuildInviteUrlTests(unittest.TestCase):
    def test_contains_client_id_scopes_and_permissions(self) -> None:
        query = parse_qs(urlparse(build_invite_url(123)).query)
        self.assertEqual(query["client_id"], ["123"])
        self.assertEqual(query["scope"], ["bot applications.commands"])
        self.assertEqual(query["permissions"], [str(INVITE_PERMISSIONS.value)])


if __name__ == "__main__":
    unittest.main()
