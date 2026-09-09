#!/usr/bin/env python

import unittest
from unittest.mock import patch, MagicMock
from spotify2ytmusic import backend


class TestCopier(unittest.TestCase):
    @patch("spotify2ytmusic.backend.lookup_song")
    def test_copier_skips_track_already_in_destination(self, mock_lookup_song):
        yt = MagicMock()
        yt.get_playlist.return_value = {
            "title": "Test Playlist",
            "tracks": [{"videoId": "already-there"}],
        }
        mock_lookup_song.return_value = {
            "videoId": "already-there",
            "title": "Test Track",
            "artists": [{"name": "Test Artist"}],
            "album": "Test Album",
        }

        backend.copier(
            [backend.SongInfo("Test Track", "Test Artist", "Test Album")],
            dst_pl_id="dst_test",
            yt=yt,
            track_sleep=0,
        )

        yt.add_playlist_items.assert_not_called()

    @patch("spotify2ytmusic.backend.YTMusic")
    def test_copier_success(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        backend.copier(
            backend.iter_spotify_playlist(
                "68QlHDwCiXfhodLpS72iOx",
                spotify_playlist_file="tests/playliststest.json",
            ),
            dst_pl_id="dst_test",
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )

    @patch("spotify2ytmusic.backend.YTMusic")
    def test_copier_albums(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        backend.copier(
            backend.iter_spotify_liked_albums(
                spotify_playlist_file="tests/playliststest.json"
            ),
            dst_pl_id="dst_test",
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )

    @patch("spotify2ytmusic.backend.YTMusic")
    def test_copier_liked_playlists(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        backend.copier(
            backend.iter_spotify_playlist(
                None, spotify_playlist_file="tests/playliststest.json"
            ),
            dst_pl_id="dst_test",
            track_sleep=0,
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )


if __name__ == "__main__":
    unittest.main()
