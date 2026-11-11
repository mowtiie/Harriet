"""Tests for query classification and local file lookup."""

import tempfile
import unittest
from pathlib import Path

from playback.resolver import find_local_file, is_web_url, matching_local_names, resolve_track


class IsWebUrlTests(unittest.TestCase):
    def test_http_and_https_are_urls(self) -> None:
        self.assertTrue(is_web_url("https://youtu.be/abc"))
        self.assertTrue(is_web_url("http://example.com/a.mp3"))

    def test_plain_text_and_other_schemes_are_not(self) -> None:
        self.assertFalse(is_web_url("lofi hip hop"))
        self.assertFalse(is_web_url("file:///etc/passwd"))


class LocalFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.music_dir = Path(self.directory.name) / "music"
        self.music_dir.mkdir()
        (self.music_dir / "Song One.mp3").touch()
        (self.music_dir / "other.ogg").touch()
        (Path(self.directory.name) / "secret.txt").touch()

    def test_matches_full_name_or_stem_ignoring_case(self) -> None:
        expected = self.music_dir / "Song One.mp3"
        self.assertEqual(find_local_file("song one.mp3", self.music_dir), expected)
        self.assertEqual(find_local_file("SONG ONE", self.music_dir), expected)

    def test_unknown_file_returns_none(self) -> None:
        self.assertIsNone(find_local_file("missing", self.music_dir))

    def test_cannot_escape_the_music_folder(self) -> None:
        self.assertIsNone(find_local_file("../secret.txt", self.music_dir))

    def test_missing_folder_returns_none(self) -> None:
        self.assertIsNone(find_local_file("song", self.music_dir / "nope"))

    def test_matching_names_filters_and_sorts(self) -> None:
        names = matching_local_names(self.music_dir, "", 25)
        self.assertEqual(names, ["Song One.mp3", "other.ogg"])
        self.assertEqual(matching_local_names(self.music_dir, "OTHER", 25), ["other.ogg"])
        self.assertEqual(matching_local_names(self.music_dir, "", 1), ["Song One.mp3"])


class ResolveLocalTrackTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_file_becomes_a_local_track(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            music_dir = Path(directory)
            (music_dir / "tune.mp3").touch()
            track = await resolve_track("tune", music_dir, "tester")
        self.assertTrue(track.is_local)
        self.assertEqual(track.title, "tune")
        self.assertEqual(track.requested_by, "tester")


if __name__ == "__main__":
    unittest.main()
