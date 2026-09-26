#!/usr/bin/env python

import unittest
from unittest.mock import patch, MagicMock

from spotify2ytmusic import backend
from spotify2ytmusic.backend import SongInfo

TRACK = SongInfo("Song A", "Artist 1", "Album X")


def fake_lookup(yt, title, artist, album, algo, details=None):
    return {"videoId": f"vid-{title}", "title": title, "artists": [{"name": artist}]}


class TestPlaylistTitles(unittest.TestCase):
    def test_create_replaces_angle_brackets(self):
        yt = MagicMock()
        yt.create_playlist.return_value = "PL_new"
        with patch.object(backend.time, "sleep"):
            backend._ytmusic_create_playlist(yt, "Marceline songs <3", "Marceline songs <3")

        kwargs = yt.create_playlist.call_args.kwargs
        self.assertEqual(kwargs["title"], "Marceline songs ‹3")
        self.assertEqual(kwargs["description"], "Marceline songs ‹3")

    def test_lookup_finds_renamed_playlist(self):
        yt = MagicMock()
        yt.get_library_playlists.return_value = [
            {"title": "Marceline songs ‹3", "playlistId": "PL_existing"}
        ]
        self.assertEqual(
            backend.get_playlist_id_by_name(yt, "Marceline songs <3"), "PL_existing"
        )

    def test_create_strips_whitespace(self):
        yt = MagicMock()
        yt.create_playlist.return_value = "PL_new"
        with patch.object(backend.time, "sleep"):
            backend._ytmusic_create_playlist(yt, "Coding Mode  ", "Coding Mode  ")

        self.assertEqual(yt.create_playlist.call_args.kwargs["title"], "Coding Mode")

    def test_lookup_matches_despite_stray_whitespace(self):
        #  A title that still has whitespace should find a playlist YTMusic stored
        #  trimmed, and a trimmed lookup title should still find it either way.
        yt = MagicMock()
        yt.get_library_playlists.return_value = [
            {"title": "Coding Mode", "playlistId": "PL_existing"}
        ]
        self.assertEqual(
            backend.get_playlist_id_by_name(yt, "Coding Mode  "), "PL_existing"
        )
        self.assertEqual(
            backend.get_playlist_id_by_name(yt, "Coding Mode"), "PL_existing"
        )


class TestCopier(unittest.TestCase):
    def run_copier(self, yt, dst_pl_id="PL_test"):
        with patch.object(backend, "lookup_song", side_effect=fake_lookup), patch.object(
            backend.time, "sleep"
        ) as sleep:
            backend.copier(iter([TRACK]), dst_pl_id, track_sleep=0, yt=yt)
        return sleep

    def test_waits_for_new_playlist(self):
        yt = MagicMock()
        yt.get_playlist.side_effect = [KeyError("contents"), {"title": "Test Playlist"}]

        self.run_copier(yt)

        self.assertEqual(yt.get_playlist.call_count, 2)
        yt.add_playlist_items.assert_called_once()

    def test_gives_up_on_missing_playlist(self):
        yt = MagicMock()
        yt.get_playlist.side_effect = KeyError("contents")

        with self.assertRaises(SystemExit):
            self.run_copier(yt)
        self.assertEqual(yt.get_playlist.call_count, 5)

    def test_expired_login_stops_without_retrying(self):
        yt = MagicMock()
        yt.get_playlist.return_value = {"title": "Test Playlist"}
        yt.add_playlist_items.side_effect = Exception(
            "Server returned HTTP 401: Unauthorized."
        )

        with self.assertRaises(SystemExit) as cm:
            self.run_copier(yt)
        self.assertEqual(cm.exception.code, 2)
        yt.add_playlist_items.assert_called_once()

    def test_other_errors_still_retry(self):
        yt = MagicMock()
        yt.get_playlist.return_value = {"title": "Test Playlist"}
        yt.add_playlist_items.side_effect = [Exception("HTTP 500"), None]

        self.run_copier(yt)

        self.assertEqual(yt.add_playlist_items.call_count, 2)


if __name__ == "__main__":
    unittest.main()
