#!/usr/bin/env python

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from spotify2ytmusic import backend
from spotify2ytmusic.backend import SongInfo, CopyProgress

TRACKS = [
    SongInfo("Song A", "Artist 1", "Album X"),
    SongInfo("Song B", "Artist 2", "Album Y"),
    SongInfo("Song C", "Artist 3", "Album Z"),
]


def fake_lookup(yt, title, artist, album, algo, details=None):
    return {"videoId": f"vid-{title}", "title": title, "artists": [{"name": artist}]}


class TestCopyProgress(unittest.TestCase):
    def setUp(self):
        fd, self.progress_file = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        os.remove(self.progress_file)

    def tearDown(self):
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    def run_copier(self, tracks, dst_pl_id="PL_test", dry_run=False, yt=None):
        yt = yt or MagicMock()
        yt.get_playlist.return_value = {"title": "Test Playlist"}
        with patch.object(backend, "lookup_song", side_effect=fake_lookup) as lookup:
            backend.copier(
                iter(tracks),
                dst_pl_id,
                dry_run=dry_run,
                track_sleep=0,
                yt=yt,
                progress_file=self.progress_file,
            )
        return yt, lookup

    def test_resume_skips_copied_tracks(self):
        self.run_copier(TRACKS[:2])
        yt, lookup = self.run_copier(TRACKS)

        self.assertEqual(lookup.call_count, 1)
        yt.add_playlist_items.assert_called_once_with(
            playlistId="PL_test", videoIds=["vid-Song C"], duplicates=False
        )

    def test_progress_is_per_destination(self):
        self.run_copier(TRACKS)
        _, lookup = self.run_copier(TRACKS, dst_pl_id="PL_other")
        self.assertEqual(lookup.call_count, 3)

    def test_liked_songs_progress(self):
        self.run_copier(TRACKS[:1], dst_pl_id=None)
        yt, lookup = self.run_copier(TRACKS, dst_pl_id=None)

        self.assertEqual(lookup.call_count, 2)
        self.assertEqual(yt.rate_song.call_count, 2)

    def test_dry_run_records_nothing(self):
        self.run_copier(TRACKS, dry_run=True)
        self.assertFalse(os.path.exists(self.progress_file))

    def test_failed_add_is_not_recorded(self):
        yt = MagicMock()
        yt.add_playlist_items.side_effect = Exception("boom")
        with patch.object(backend.time, "sleep"):
            self.run_copier(TRACKS[:1], yt=yt)
        self.assertFalse(CopyProgress(self.progress_file).is_done("PL_test", TRACKS[0]))

    def test_truncated_line_is_ignored(self):
        self.run_copier(TRACKS[:1])
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write('{"dst": "PL_test", "title": "Song B"')

        progress = CopyProgress(self.progress_file)
        self.assertTrue(progress.is_done("PL_test", TRACKS[0]))
        self.assertFalse(progress.is_done("PL_test", TRACKS[1]))

        # Entries written after the truncated line must still be readable.
        progress.mark_done("PL_test", TRACKS[2], "vid-Song C")
        self.assertTrue(CopyProgress(self.progress_file).is_done("PL_test", TRACKS[2]))

    def test_non_ascii_titles_round_trip(self):
        track = SongInfo("شايفة الدنيا خضرا", "The Synaptik", "名探偵コナン")
        self.run_copier([track])
        self.assertTrue(CopyProgress(self.progress_file).is_done("PL_test", track))

    def test_disabled_progress_writes_no_file(self):
        progress = CopyProgress(None)
        progress.mark_done("PL_test", TRACKS[0], "vid")
        self.assertTrue(progress.is_done("PL_test", TRACKS[0]))
        self.assertFalse(os.path.exists(backend.DEFAULT_PROGRESS_FILE))


if __name__ == "__main__":
    unittest.main()
