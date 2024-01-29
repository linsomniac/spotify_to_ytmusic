#!/usr/bin/env python3

import json
import sys
import os
import time
import re
from argparse import ArgumentParser
from ytmusicapi import YTMusic
from typing import Optional, Union, Iterator
from collections import namedtuple


SongInfo = namedtuple("SongInfo", ["title", "artist", "album"])


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


def list_liked_albums():
    """
    List albums that have been liked.
    """
    for song in iter_spotify_liked_albums():
        print(f"{song.album} - {song.artist} - {song.title}")


def list_playlists():
    """
    List the playlists on Spotify and YTMusic
    """
    yt = get_ytmusic()

    spotify_pls = load_playlists_json()

    #  Liked music
    print("== Spotify playlists")
    for src_pl in spotify_pls["playlists"]:
        print(
            f"{src_pl.get('id')} - {src_pl['name']:50} ({len(src_pl['tracks'])} tracks)"
        )

    print()
    print("== YTMusic")
    for pl in yt.get_library_playlists(limit=5000):
        print(f"{pl['playlistId']} - {pl['title']:40} ({pl.get('count', '?')} tracks)")


def _ytmusic_create_playlist(yt: YTMusic, title: str, description: str) -> str:
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


def create_playlist(pl_name="", use_param=False) -> None:
    """
    Create a YTMusic playlist
    """
    if not use_param:
        if len(sys.argv) == 2:
            pl_name = sys.argv[1]
        else:
            print(f"usage: {os.path.basename(sys.argv[0])} <YT PLAYLIST NAME>")
            sys.exit(1)

    yt = get_ytmusic()

    id = _ytmusic_create_playlist(yt, title=pl_name, description=pl_name)
    print(f"Playlist ID: {id}")


def lookup_song(yt, track_name: str, artist_name: str, album_name: str):
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
    
    # Finds exact match
    for album in albums[:3]:

        try:
            for track in yt.get_album(album["browseId"])["tracks"]:
                if track["title"] == track_name:
                    return track
            # print(f"{track['videoId']} - {track['title']} - {track['artists'][0]['name']}")
        except Exception as e:
            print(f"Unable to lookup album ({e}), continuing...")

    songs = yt.search(query=f"{track_name} by {artist_name}", filter="songs")
    # print(songs)
    
    #  This would need to do fuzzy matching
    for song in songs:
        # Remove everything in brackets in the song title
        song_title_without_brackets = re.sub(r'[\[\(].*?[\]\)]', '', song["title"])
        if ((
            song_title_without_brackets == track_name
            and song["album"]["name"] == album_name
        ) or (
            song_title_without_brackets == track_name
        ) or (
            song_title_without_brackets in track_name
        ) or (
            track_name in song_title_without_brackets
        )) and (
            song["artists"][0]["name"] == artist_name or artist_name in song["artists"][0]["name"]
        ):
            return song

    # Finds approximate match
    # This tries to find a song anyway. Works when the song is not released as a music but a video.
    else:
        track_name = track_name.lower()
        first_song_title = songs[0]["title"].lower()
        if track_name not in first_song_title or songs[0]["artists"][0]["name"] != artist_name: # If the first song is not the one we are looking for
            print("Not found in songs, searching videos")
            new_songs = yt.search(query=f"{track_name} by {artist_name}", filter="videos") # Search videos
            
            # From here, we search for videos reposting the song. They often contain the name of it and the artist. Like with 'Nekfeu - Ecrire'.
            for new_song in new_songs:
                new_song_title = new_song["title"].lower() # People sometimes mess up the capitalization in the title
                if (track_name in new_song_title and artist_name in new_song_title) or (track_name in new_song_title):
                    print("Found a video")
                    return new_song
            else: 
                # Basically we only get here if the song isnt present anywhere on youtube
                raise ValueError(f"Did not find {track_name} by {artist_name} from {album_name}")
        else:
            return songs[0]


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


def load_liked_albums():
    """
    Load the "Liked" albums from Spotify into YTMusic.  Spotify stores liked albums separately
    from liked songs, so "load_liked" does not see the albums, you instead need to use this.
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
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )

        return parser.parse_args()

    args = parse_arguments()

    spotify_pls = load_playlists_json()

    copier(
        iter_spotify_liked_albums(spotify_encoding=args.spotify_playlists_encoding),
        None,
        args.dry_run,
        args.track_sleep,
    )


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
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )

        return parser.parse_args()

    args = parse_arguments()
    dry_run = args.dry_run
    track_sleep = args.track_sleep
    spotify_playlists_encoding = args.spotify_playlists_encoding

    copier(
        iter_spotify_playlist(None, spotify_encoding=spotify_playlists_encoding),
        None,
        dry_run,
        track_sleep,
    )


def lookup_playlist(yt: YTMusic, pl_name: str) -> str:
    dst_pl_id = get_playlist_id_by_name(yt, pl_name)
    print(f"Looking up playlist '{pl_name}': id={dst_pl_id}")
    if dst_pl_id == "":
        dst_pl_id = _ytmusic_create_playlist(yt, title=pl_name, description=pl_name)
        time.sleep(1)  # seems to be needed to avoid missing playlist ID error

        #  create_playlist returns a dict if there was an error
        if isinstance(dst_pl_id, dict):
            print(f"ERROR: Failed to create playlist: {dst_pl_id}")
            sys.exit(1)
        print(f"NOTE: Created playlist '{pl_name}' with ID: {dst_pl_id}")
    return dst_pl_id


def copy_playlist(src_pl_id="", dst_pl_id=""):
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
            "-i", "--spotify_playlist_id",
            type=str,
            default="",
            help="ID of the Spotify playlist to copy from",
        )
        parser.add_argument(
            "-o", "--ytmusic_playlist_id",
            type=str,
            default="",
            help="ID of the YTMusic playlist to copy to.  If this argument starts with a '+', it is assumed to be the playlist title rather than playlist ID, and if a playlist of that name is not found, it will be created (without the +).  Example: '+My Favorite Blues'.  NOTE: The shell will require you to quote the name if it contains spaces.",
        )
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )

        return parser.parse_args()

    args = parse_arguments()
    if src_pl_id == "":
        src_pl_id = args.spotify_playlist_id
    if dst_pl_id == "":
        dst_pl_id = args.ytmusic_playlist_id
    dry_run = args.dry_run
    track_sleep = args.track_sleep
    spotify_playlists_encoding = args.spotify_playlists_encoding
    
    print(dst_pl_id)

    yt = get_ytmusic()
    if dst_pl_id.startswith("+"):
        pl_name = dst_pl_id[1:]

        lookup_playlist(yt, pl_name)

    copier(
        iter_spotify_playlist(
            src_pl_id, spotify_encoding=spotify_playlists_encoding
        ),
        dst_pl_id,
        dry_run,
        track_sleep,
        yt=yt,
    )


def copy_all_playlists():
    """
    Copy all Spotify playlists (except Liked Songs) to YTMusic playlists
    """
    yt = get_ytmusic()

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "-i", "--input",
            type=str,
            default="playlists.json",
            help="Filename of Spotify playlists.json file")
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
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )

        return parser.parse_args()

    args = parse_arguments()
    dry_run = args.dry_run
    track_sleep = args.track_sleep
    spotify_playlists_encoding = args.spotify_playlists_encoding
    input_file = args.input

    spotify_pls = load_playlists_json(filename=input_file)

    for src_pl in spotify_pls["playlists"]:
        if str(src_pl.get("name")) == "Liked Songs":
            continue

        pl_name = src_pl["name"]
        if pl_name == "":
            pl_name = f"Unnamed Spotify Playlist {src_pl['id']}"

        dst_pl_id = lookup_playlist(yt, pl_name)

        copier(
            iter_spotify_playlist(
                src_pl["id"], spotify_encoding=spotify_playlists_encoding
            ),
            dst_pl_id,
            dry_run,
            track_sleep,
        )
        print("\nPlaylist done!\n")

    print("All done!")


def load_playlists_json(filename: str = "playlists.json", encoding: str = "utf-8"):
    """Load the `playlists.json` Spotify playlist file"""
    return json.load(open(filename, "r", encoding=encoding))


def copier(
    src_tracks: Iterator[SongInfo],
    dst_pl_id: Optional[str] = "",
    dry_run: bool = False,
    track_sleep: float = 0.1,
    *,
    yt: Optional[YTMusic] = None,
):
    if yt is None:
        yt = get_ytmusic()

    if dst_pl_id != "":
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

    for src_track in src_tracks:
        print(f"Spotify:   {src_track.title} - {src_track.artist} - {src_track.album}")

        try:
            dst_track = lookup_song(
                yt, src_track.title, src_track.artist, src_track.album
            )
        except Exception as e:
            print(f"ERROR: Unable to look up song on YTMusic: {e}")
            error_count += 1
            continue

        yt_artist_name = "<Unknown>"
        if "artists" in dst_track and len(dst_track["artists"]) > 0:
            yt_artist_name = dst_track["artists"][0]["name"]
        print(
            f"  Youtube: {dst_track['title']} - {yt_artist_name} - {dst_track['album'] if 'album' in dst_track.keys() else 'No album'}"
        )

        if dst_track["videoId"] in tracks_added_set:
            print("(DUPLICATE, this track has already been added)")
            duplicate_count += 1
        tracks_added_set.add(dst_track["videoId"])

        if not dry_run:
            exception_sleep = 5
            for _ in range(10):
                try:
                    if dst_pl_id != "":
                        yt.add_playlist_items(
                            playlistId=dst_pl_id,
                            videoIds=[dst_track["videoId"]],
                            duplicates=False,
                        )
                    else:
                        yt.rate_song(dst_track["videoId"], "LIKE")
                    break
                except Exception as e:
                    print(
                        f"ERROR: (Retrying add_playlist_items: {dst_pl_id} {dst_track['videoId']}) {e} in {exception_sleep} seconds"
                    )
                    time.sleep(exception_sleep)
                    exception_sleep *= 2

        if track_sleep:
            time.sleep(track_sleep)

    print()
    print(
        f"Added {len(tracks_added_set)} tracks, encountered {duplicate_count} duplicates, {error_count} errors"
    )
