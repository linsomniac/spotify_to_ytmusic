#!/usr/bin/env python3

import json
import sys
import os
import time
from argparse import ArgumentParser
from ytmusicapi import YTMusic
from typing import Optional, Union, Iterator
from collections import namedtuple


SongInfo = namedtuple("SongInfo", ["title", "artist", "album"])


def _ytmusic_create_playlist(yt: YTMusic, title: str, description: str) -> str:
    """Wrapper on ytmusic.create_playlist

    This wrapper does retries with back-off because sometimes YouTube Music will
    rate limit requests or otherwise fail.
    """

    def _create(yt: YTMusic, title: str, description: str) -> Union[str, dict]:
        exception_sleep = 5
        for _ in range(10):
            try:
                """Create a playlist on YTMusic, retrying if it fails."""
                id = yt.create_playlist(title=title, description=description)
                return id
            except Exception as e:
                print(
                    f"ERROR: (Retrying create_playlist: {title}) {e} in {exception_sleep} seconds"
                )
                time.sleep(exception_sleep)
                exception_sleep *= 2

        return {
            "s2yt error": 'ERROR: Could not create playlist "{title}" after multiple retries'
        }

    id = _create(yt, title, description)
    #  create_playlist returns a dict if there was an error
    if isinstance(id, dict):
        print(f"ERROR: Failed to create playlist (name: {title}): {id}")
        sys.exit(1)

    time.sleep(1)  # seems to be needed to avoid missing playlist ID error

    return id


def load_playlists_json(filename: str = "playlists.json", encoding: str = "utf-8"):
    """Load the `playlists.json` Spotify playlist file"""
    return json.load(open(filename, "r", encoding=encoding))


def create_playlist(pl_name: str):
    """
    Create a YTMusic playlist
    """
    yt = get_ytmusic()

    id = _ytmusic_create_playlist(yt, title=pl_name, description=pl_name)
    print(f"Playlist ID: {id}")


def get_ytmusic() -> YTMusic:
    if not os.path.exists("oauth.json"):
        print("ERROR: No file 'oauth.json' exists in the current directory.")
        print("       Have you logged in to YTMusic?  Run 'ytmusicapi oauth' to login")
        sys.exit(1)

    try:
        return YTMusic("oauth.json")
    except json.decoder.JSONDecodeError as e:
        print(f"ERROR: JSON Decode error while trying start YTMusic: {e}")
        print("       This typically means a problem with a 'oauth.json' file.")
        print("       Have you logged in to YTMusic?  Run 'ytmusicapi oauth' to login")
        sys.exit(1)


def iter_spotify_liked_albums(
    spotify_playlist_file: str = "playlists.json",
    spotify_encoding: str = "utf-8",
) -> Iterator[SongInfo]:
    """Songs from liked albums on Spotify."""
    spotify_pls = load_playlists_json(spotify_playlist_file, spotify_encoding)

    if not "albums" in spotify_pls:
        return None

    for album in [x["album"] for x in spotify_pls["albums"]]:
        for track in album["tracks"]["items"]:
            yield SongInfo(track["name"], track["artists"][0]["name"], album["name"])


def iter_spotify_playlist(
    src_pl_id: Optional[str] = None,
    spotify_playlist_file: str = "playlists.json",
    spotify_encoding: str = "utf-8",
) -> Iterator[SongInfo]:
    """Songs from a specific album ("Liked Songs" if None)"""
    spotify_pls = load_playlists_json(spotify_playlist_file, spotify_encoding)

    for src_pl in spotify_pls["playlists"]:
        if src_pl_id is None:
            if str(src_pl.get("name")) != "Liked Songs":
                continue
        else:
            if str(src_pl.get("id")) != src_pl_id:
                continue

        src_pl_name = src_pl["name"]

        print(f"== Spotify Playlist: {src_pl_name}")

        for src_track in reversed(src_pl["tracks"]):
            if src_track["track"] is None:
                print(
                    f"WARNING: Spotify track seems to be malformed, Skipping.  Track: {src_track!r}"
                )
                continue

            try:
                src_album_name = src_track["track"]["album"]["name"]
                src_track_artist = src_track["track"]["artists"][0]["name"]
            except TypeError as e:
                print(
                    f"ERROR: Spotify track seems to be malformed.  Track: {src_track!r}"
                )
                raise (e)
            src_track_name = src_track["track"]["name"]

            yield SongInfo(src_track_name, src_track_artist, src_album_name)
