Tools for moving from Spotify to YTMusic

# Overview

This is a set of scripts for copying "liked" songs and playlists from Spotify to YTMusic.

# Getting Started

## Install ytmusicapi

`pip install ytmusicapi`

## Login to YTMusic

`ytmusicapi oauth`

This will give you a URL, visit that URL and authorize the application.  When you are
done with the import you can remove the authorization for this app.

This will write a file "oauth.json".  Keep this file secret while the app is authorized.
This file includes a logged in session token.

## Backup Your Spotify Playlists

Download
[https://raw.githubusercontent.com/caseychu/spotify-backup/master/spotify-backup.py](spotify-backup).

Run `spotify-backup.py` and it will help you authorize access to your spotify account.

Run: `python3 spotify-backup.py playlists.json --dump=liked,playlists --format=json`

This will save your playlists and liked songs into the file "playlists.json".

## Import Your Liked Songs

Run: `python3 load_liked`

It will go through your Spotify liked songs, and like them on YTMusic.  It will display
the song from spotify and then the song that it found on YTMusic that it is liking.  I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify.  So far I haven't seen a single failure across a couple thousand songs, but more
esoteric titles it may have issues with.

## List Your Playlists

Run `python3 list_playlists`

This will list the playlists you have on both Spotify and YTMusic.  You will need to
individually copy them.  Find the "playlist id" (the first column) of the Spotify
playlist, and of the YTMusic playlist, and then run:

`python3 copy_playlist <SPOTIFY_PLAYLIST_ID> <YTMUSIC_PLAYLIST_ID>`

If you need to create a playlist, run:

`python3 create_playlist "<PLAYLIST_NAME>"`

Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.

## FAQ

- My copy is failing with repeated "ERROR: (Retrying) Server returned HTTP 400: Bad
  Request".

  Try running with "--track-sleep=3" argument to do a 3 second sleep between tracks.  This
  will take much longer, but may succeed where faster rates have failed.

[//]: # ( vim: set tw=90 ts=4 sw=4 ai: )
