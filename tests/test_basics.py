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
            src_pl_id="68QlHDwCiXfhodLpS72iOx",
            dst_pl_id="dst_test",
            spotify_playlist_file="tests/playliststest.json",
        )

        mock_ytmusic_instance.get_playlist.assert_called_once_with(
            playlistId="dst_test"
        )


if __name__ == "__main__":
    unittest.main()
