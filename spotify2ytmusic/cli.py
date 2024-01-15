#!/usr/bin/env python3

import json
import sys
import os
import time
from argparse import ArgumentParser
from ytmusicapi import YTMusic
from typing import Optional, Union


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


def get_playlist_id_by_name(yt: YTMusic, title: str) -> Optional[str]:
    """Look up a YTMusic playlist ID by name.  Return None if not found."""
    for pl in yt.get_library_playlists(limit=5000):
        if pl["title"] == title:
            return pl["playlistId"]

    return None


def list_playlists():
    """
    List the playlists on Spotify and YTMusic
    """
    yt = get_ytmusic()

    spotify_pls = json.load(open("playlists.json", "r"))

    #  Liked music
    print("== Spotify")
    for src_pl in spotify_pls["playlists"]:
        print(
            f"{src_pl.get('id')} - {src_pl['name']:50} ({len(src_pl['tracks'])} tracks)"
        )

    print()
    print("== YTMusic")
    for pl in yt.get_library_playlists(limit=5000):
        print(f"{pl['playlistId']} - {pl['title']:40} ({pl.get('count', '?')} tracks)")


def create_playlist():
    """
    Create a YTMusic playlist
    """
    if len(sys.argv) != 2:
        print(f"usage: {os.path.basename(sys.argv[0])} <YT PLAYLIST NAME>")
        sys.exit(1)

    pl_name = sys.argv[1]

    yt = get_ytmusic()

    id = yt.create_playlist(title=pl_name, description=pl_name)
    print(f"Playlist ID: {id}")


def lookup_song(yt, track_name, artist_name, album_name):
    """Look up a song on YTMusic

    Given the Spotify track information, it does a lookup for the album by the same
    artist on YTMusic, then looks at the first 3 hits looking for a track with exactly
    the same name. In the event that it can't find that exact track, it then does
    a search of songs for the track name by the same artist and simply returns the
    first hit.

    The idea is that finding the album and artist and then looking for the exact track
    match will be more likely to be accurate than searching for the song and artist and
    relying on the YTMusic algorithm to figure things out, especially for short tracks
    that might be have many contradictory hits like "Survival by Yes".
    """
    albums = yt.search(query=f"{album_name} by {artist_name}", filter="albums")
    for album in albums[:3]:
        # print(album)
        # print(f"ALBUM: {album['browseId']} - {album['title']} - {album['artists'][0]['name']}")

        try:
            for track in yt.get_album(album["browseId"])["tracks"]:
                if track["title"] == track_name:
                    return track
            # print(f"{track['videoId']} - {track['title']} - {track['artists'][0]['name']}")
        except Exception as e:
            print(f"Unable to lookup album ({e}), continuing...")

    songs = yt.search(query=f"{track_name} by {artist_name}", filter="songs")
    return songs[0]

    #  This would need to do fuzzy matching
    for song in songs:
        if (
            song["title"] == track_name
            and song["artists"][0]["name"] == artist_name
            and song["album"]["name"] == album_name
        ):
            return song
        # print(f"SONG: {song['videoId']} - {song['title']} - {song['artists'][0]['name']} - {song['album']['name']}")

    raise ValueError(f"Did not find {track_name} by {artist_name} from {album_name}")


def search():
    """Search for a track on ytmusic"""

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "track_name",
            type=str,
            help="Name of track to search for",
        )
        parser.add_argument(
            "--artist",
            type=str,
            help="Artist to look up",
        )
        parser.add_argument(
            "--album",
            type=str,
            help="Album name",
        )
        return parser.parse_args()

    args = parse_arguments()

    yt = get_ytmusic()
    ret = lookup_song(yt, args.track_name, args.artist, args.album)
    print(ret)


def load_liked():
    """
    Load the "Liked Songs" playlist from Spotify into YTMusic.
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )

        return parser.parse_args()

    args = parse_arguments()

    copier(None, None, args.dry_run, args.track_sleep)


def copy_playlist():
    """
    Copy a Spotify playlist to a YTMusic playlist
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "spotify_playlist_id",
            type=str,
            help="ID of the Spotify playlist to copy from",
        )
        parser.add_argument(
            "ytmusic_playlist_id",
            type=str,
            help="ID of the YTMusic playlist to copy to.  If this argument starts with a '+', it is asumed to be the playlist title rather than playlist ID, and if a playlist of that name is not found, it will be created (without the +).  Example: '+My Favorite Blues'.  NOTE: The shell will require you to quote the name if it contains spaces.",
        )

        return parser.parse_args()

    args = parse_arguments()
    src_pl_id = args.spotify_playlist_id
    dst_pl_id = args.ytmusic_playlist_id

    yt = get_ytmusic()
    if dst_pl_id.startswith("+"):
        pl_name = dst_pl_id[1:]

        dst_pl_id = get_playlist_id_by_name(yt, pl_name)
        print(f"Looking up playlist '{pl_name}': id={dst_pl_id}")
        if dst_pl_id is None:
            dst_pl_id = yt.create_playlist(title=pl_name, description=pl_name)
            time.sleep(1)  # seems to be needed to avoid missing playlist ID error

            #  create_playlist returns a dict if there was an error
            if isinstance(dst_pl_id, dict):
                print(f"ERROR: Failed to create playlist: {dst_pl_id}")
                sys.exit(1)
            print(f"NOTE: Created playlist '{pl_name}' with ID: {dst_pl_id}")

    copier(src_pl_id, dst_pl_id, args.dry_run, args.track_sleep, yt=yt)


def copy_all_playlists():
    """
    Copy all Spotify playlists (except Liked Songs) to YTMusic playlists
    """
    yt = YTMusic("oauth.json")

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )

        return parser.parse_args()

    args = parse_arguments()
    spotify_pls = json.load(open("playlists.json", "r"))

    for src_pl in spotify_pls["playlists"]:
        if str(src_pl.get("name")) == "Liked Songs":
            continue

        pl_name = src_pl["name"]
        dst_pl_id = get_playlist_id_by_name(yt, pl_name)
        print(f"Looking up playlist '{pl_name}': id={dst_pl_id}")
        if dst_pl_id is None:
            dst_pl_id = yt.create_playlist(title=pl_name, description=pl_name)
            time.sleep(1)  # seems to be needed to avoid missing playlist ID error

            #  create_playlist returns a dict if there was an error
            if isinstance(dst_pl_id, dict):
                print(f"ERROR: Failed to create playlist: {dst_pl_id}")
                sys.exit(1)
            print(f"NOTE: Created playlist '{pl_name}' with ID: {dst_pl_id}")

        copier(src_pl["id"], dst_pl_id, args.dry_run, args.track_sleep)
        print("\nPlaylist done!\n")

    print("All done!")


def copier(
    src_pl_id: Optional[str] = None,
    dst_pl_id: Optional[str] = None,
    dry_run: bool = False,
    track_sleep: float = 0.1,
    spotify_playlist_file: str = "playlists.json",
    *,
    yt: Optional[YTMusic] = None,
):
    if yt is None:
        yt = get_ytmusic()

    spotify_pls = json.load(open(spotify_playlist_file, "r"))
    if dst_pl_id is not None:
        try:
            yt_pl = yt.get_playlist(playlistId=dst_pl_id)
        except Exception as e:
            print(f"ERROR: Unable to find YTMusic playlist {dst_pl_id}: {e}")
            print(
                "       Make sure the YTMusic playlist ID is correct, it should be something like "
            )
            print("      'PL_DhcdsaJ7echjfdsaJFhdsWUd73HJFca'")
            sys.exit(1)
        print(f"== Youtube Playlist: {yt_pl['title']}")

    tracks_added_set = set()
    duplicate_count = 0
    error_count = 0

    for src_pl in spotify_pls["playlists"]:
        if src_pl_id is None:
            if str(src_pl.get("name")) != "Liked Songs":
                continue
        else:
            if str(src_pl.get("id")) != src_pl_id:
                continue

        src_pl_name = src_pl["name"]

        print(f"== Spotify Playlist: {src_pl_name}")

        for src_track in src_pl["tracks"]:
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

            print(
                f"Spotify:   {src_track_name} - {src_track_artist} - {src_album_name}"
            )

            try:
                dst_track = lookup_song(
                    yt, src_track_name, src_track_artist, src_album_name
                )
            except Exception as e:
                print(f"ERROR: Unable to look up song on YTMusic: {e}")
                error_count += 1
                continue

            yt_artist_name = "<Unknown>"
            if "artists" in dst_track and len(dst_track["artists"]) > 0:
                yt_artist_name = dst_track["artists"][0]["name"]
            print(
                f"  Youtube: {dst_track['title']} - {yt_artist_name} - {dst_track['album']}"
            )

            if dst_track["videoId"] in tracks_added_set:
                print("(DUPLICATE, this track has already been added)")
                duplicate_count += 1
            tracks_added_set.add(dst_track["videoId"])

            if not dry_run:
                exception_sleep = 5
                for _ in range(10):
                    try:
                        if dst_pl_id is not None:
                            yt.add_playlist_items(
                                playlistId=dst_pl_id,
                                videoIds=[dst_track["videoId"]],
                                duplicates=False,
                            )
                        else:
                            yt.rate_song(dst_track["videoId"], "LIKE")
                        break
                    except Exception as e:
                        print(f"ERROR: (Retrying) {e} in {exception_sleep} seconds")
                        time.sleep(exception_sleep)
                        exception_sleep *= 2

            if track_sleep:
                time.sleep(track_sleep)

    print()
    print(
        f"Added {len(tracks_added_set)} tracks, encountered {duplicate_count} duplicates, {error_count} errors"
    )
