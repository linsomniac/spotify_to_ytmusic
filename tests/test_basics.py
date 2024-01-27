#!/usr/bin/env python

import unittest
from unittest.mock import patch, MagicMock
import spotify2ytmusic


class TestCopier(unittest.TestCase):
    @patch("spotify2ytmusic.cli.YTMusic")
    def test_copier_success(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        spotify2ytmusic.cli.copier(
            spotify2ytmusic.cli.iter_spotify_playlist(
                "68QlHDwCiXfhodLpS72iOx",
                spotify_playlist_file="tests/playliststest.json",
            ),
            dst_pl_id="dst_test",
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )

    @patch("spotify2ytmusic.cli.YTMusic")
    def test_copier_albums(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        spotify2ytmusic.cli.copier(
            spotify2ytmusic.cli.iter_spotify_liked_albums(
                spotify_playlist_file="tests/playliststest.json"
            ),
            dst_pl_id="dst_test",
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )

    @patch("spotify2ytmusic.cli.YTMusic")
    def test_copier_liked_playlists(self, mock_ytmusic):
        # Setup mock responses
        mock_ytmusic_instance = MagicMock()
        mock_ytmusic.return_value = mock_ytmusic_instance
        mock_ytmusic_instance.get_playlist.return_value = {"title": "Test Playlist"}
        mock_ytmusic_instance.add_playlist_items.return_value = None

        spotify2ytmusic.cli.copier(
            spotify2ytmusic.cli.iter_spotify_playlist(
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
