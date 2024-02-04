Tools for moving from Spotify to YTMusic

# Overview

This is a set of scripts for copying "liked" songs and playlists from Spotify to YTMusic.
It provides both CLI tools and a GUI (implemented by Yoween, formerly called
[spotify_to_ytmusic_gui](https://github.com/Yoween/spotify_to_ytmusic_gui)).

# Getting Started

## Install spotify2ytmusic (via pip)

This package is available on pip, so you can install it using:

`pip install spotify2ytmusic`

or:

`python3 -m pip install spotify2ytmusic`

## (Or) Running From Source

(Not recommended)

Another option, instead of pip, is to just clone this repo and run directly from the
source.  However, you will need the "ytmusicapi" package installed, so you'll probably
want to use pip to install that at the very least.

To run directly from source:

```shell
git clone git@github.com:linsomniac/spotify_to_ytmusic.git
cd spotify_to_ytmusic
```

Then you can prefix the command you want to run with `python3 -m spotify2ytmusic`, for
example:

```shell
python3 -m spotify2ytmusic list_playlists
python3 -m spotify2ytmusic load_liked
[etc...]
```

## Graphical UI

On Windows: `python gui.py`

Or on Linux: `python3 gui.py`

### Login to YTMusic - Tab 0

#### Click the `login` button on the first tab

OR

Enter `ytmusicapi oauth` in a console.

This will give you a URL, visit that URL and authorize the application.  When you are
done with the import you can remove the authorization for this app.

This will write a file "oauth.json".  Keep this file secret while the app is authorized.
This file includes a logged in session token.

ytmusicapi is a dependency of this software and should be installed as part of the "pip
install".

### Backup Your Spotify Playlists - Tab 1

#### Click the `Backup` button, and wait until it finished and switched to the next tab.

**OR** do all the steps below

Download
[spotify-backup](https://raw.githubusercontent.com/caseychu/spotify-backup/master/spotify-backup.py).

Run `spotify-backup.py` and it will help you authorize access to your spotify account.

Run: `python3 spotify-backup.py playlists.json --dump=liked,playlists --format=json`

This will save your playlists and liked songs into the file "playlists.json".

### Reverse your playlists - Tab 2
As mentionned below, the original program adds the songs in the 'wrong' order. That's a
feature I don't like, so I created a script to reverse them. It seems to be reliable,
but if you find anything weird, please open an issue. It creates a backup of the
original file just in case anyway.

### Import Your Liked Songs - Tab 3
#### Click the `import` button, and wait until it finished and switched to the next tab.

It will go through your Spotify liked songs, and like them on YTMusic.  It will display
the song from spotify and then the song that it found on YTMusic that it is liking.  I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify.  So far I haven't seen a single failure across a couple hundread songs, but more
esoteric titles it may have issues with.

### List Your Playlists - Tab 4

#### Click the `list` button, and wait until it finished and switched to the next tab.

This will list the playlists you have on both Spotify and YTMusic, so you can individually copy them.

### Copy Your Playlists - Tab 5

You can either copy **all** playlists, or do a more surgical copy of individual playlists.
Copying all playlists will use the name of the Spotify playlist as the destination playlist name on YTMusic.

#### To copy all the playlists click the `copy` button, and wait until it finished and switched to the next tab.

**NOTE**: This does not copy the Liked playlist (see above to do that).

### Copy specific Playlist - Tab 6

In the list output, find the "playlist id" (the first column) of the Spotify playlist and of the YTMusic playlist.
#### Then fill both input fields and click the `copy` button.

The copy playlist will take the name of the YTMusic playlist and will create the
playlist if it does not exist, if you start the YTMusic playlist with a "+":

Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.

## Command Line Usage

### Login to YTMusic

`ytmusicapi oauth`

This will give you a URL, visit that URL and authorize the application.  When you are
done with the import you can remove the authorization for this app.

This will write a file "oauth.json".  Keep this file secret while the app is authorized.
This file includes a logged in session token.

ytmusicapi is a dependency of this software and should be installed as part of the "pip
install".

### Backup Your Spotify Playlists

Download
[spotify-backup](https://raw.githubusercontent.com/caseychu/spotify-backup/master/spotify-backup.py).

Run `spotify-backup.py` and it will help you authorize access to your spotify account.

Run: `python3 spotify-backup.py playlists.json --dump=liked,playlists --format=json`

This will save your playlists and liked songs into the file "playlists.json".

### Import Your Liked Songs

Run: `s2yt_load_liked`

It will go through your Spotify liked songs, and like them on YTMusic.  It will display
the song from spotify and then the song that it found on YTMusic that it is liking.  I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify.  So far I haven't seen a single failure across a couple thousand songs, but more
esoteric titles it may have issues with.

### Import Your Liked Albums

Run: `s2yt_load_liked_albums`

Spotify stores liked albums outside of the "Liked Songs" playlist.  This is the command to
load your liked albums into YTMusic liked songs.

### List Your Playlists

Run `s2yt_list_playlists`

This will list the playlists you have on both Spotify and YTMusic.  You will need to
individually copy them.

### Copy Your Playlists

You can either copy **all** playlists, or do a more surgical copy of individual playlists.
Copying all playlists will use the name of the Spotify playlist as the destination
playlist name on YTMusic.  To copy all playlists, run:

`s2yt_copy_all_playlists`

**NOTE**: This does not copy the Liked playlist (see above to do that).

In the list output above, find the "playlist id" (the first column) of the Spotify playlist,
and of the YTMusic playlist, and then run:

`s2yt_copy_playlist <SPOTIFY_PLAYLIST_ID> <YTMUSIC_PLAYLIST_ID>`

If you need to create a playlist, you can run:

`s2yt_create_playlist "<PLAYLIST_NAME>"`

*Or* the copy playlist can take the name of the YTMusic playlist and will create the
playlist if it does not exist, if you start the YTMusic playlist with a "+":

`s2yt_copy_playlist <SPOTIFY_PLAYLIST_ID> +<YTMUSIC_PLAYLIST_NAME>`

For example:

`s2yt_copy_playlist SPOTIFY_PLAYLIST_ID "+Feeling Like a PUNK"`

Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.

### Searching for YTMusic Tracks

This is mostly for debugging, but there is a command to search for tracks in YTMusic:

`s2yt_search --artist <ARTIST> --album <ALBUM> <TRACK_NAME>`

## FAQ

- How does the lookup algorithm work?

  Given the Spotify track information, it does a lookup for the album by the same artist
  on YTMusic, then looks at the first 3 hits looking for a track with exactly the same
  name.  In the event that it can't find that exact track, it then does a search of songs
  for the track name by the same artist and simply returns the first hit.

  The idea is that finding the album and artist and then looking for the exact track match
  will be more likely to be accurate than searching for the song and artist and relying on
  the YTMusic algorithm to figure things out, especially for short tracks that might be
  have many contradictory hits like "Survival by Yes".

- My copy is failing with repeated "ERROR: (Retrying) Server returned HTTP 400: Bad
  Request".

  Try running with "--track-sleep=3" argument to do a 3 second sleep between tracks.  This
  will take much longer, but may succeed where faster rates have failed.

## License

Creative Commons Zero v1.0 Universal

spotify-backup.py licensed under MIT License
See https://github.com/caseychu/spotify-backup for more information

[//]: # ( vim: set tw=90 ts=4 sw=4 ai: )
