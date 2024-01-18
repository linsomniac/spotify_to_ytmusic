Graphical Tools for moving from Spotify to YTMusic

# Overview

This is a **fork** of the set of scripts for copying "liked" songs and playlists from Spotify to YTMusic by @linsomniac (https://github.com/linsomniac/).

What I changed :
- I created a simple graphical interface using tkinter. It's kind of ugly but it does the job.
- Created a way to invert the playlists. Since the program adds linked songs from Spotify from top to bottom, you first liked song on Spotify will be your last liked song on YT Music. More on that below.
- I changed the song search algorith. The way the original version works is by searching for exact matches, and when it doesn't find anything, it returns an error. My algorithm tries to find a match anyway and decreases in precision if nothing is found :
1) Tries to find exact match in 'songs' category (same song name, artist and album)
2) If nothing found, search in 'videos' category (same name, same artist)
3) If nothing found, keep searching but for song name and artist in video title (when the video is a repost of a song)
4) And in last resort, searches for videos with only the name of the song in the title

I've tested this process on my liked songs (500+ tracks) and so far it works. I've only had one wrong video which was a sped up version and it was using an old version of the algorith.

# Getting Started

## Running From Source (no pip available for now)

Instead of pip, is to just clone this repo and run directly from the
source.  However, you will need the "ytmusicapi" package installed, so you'll probably
want to use pip to install that at the very least.

To run directly from source:

```shell
git clone git@github.com:yoween/spotify_to_ytmusic_gui.git
cd spotify_to_ytmusic_gui
```

Then you can run the following command to start the program:

Windows:
```
python gui.py
```

Linux:
```
python3 gui.py
```
## Login to YTMusic - Tab 0

#### Click the `login` button on the first tab

OR

Enter `ytmusicapi oauth` in a console.

This will give you a URL, visit that URL and authorize the application.  When you are
done with the import you can remove the authorization for this app.

This will write a file "oauth.json".  Keep this file secret while the app is authorized.
This file includes a logged in session token.

ytmusicapi is a dependency of this software and should be installed as part of the "pip
install".

## Backup Your Spotify Playlists - Tab 1

#### Click the `Backup` button, and wait until it finished and switched to the next tab.

**OR** do all the steps below

Download
[spotify-backup](https://raw.githubusercontent.com/caseychu/spotify-backup/master/spotify-backup.py).

Run `spotify-backup.py` and it will help you authorize access to your spotify account.

Run: `python3 spotify-backup.py playlists.json --dump=liked,playlists --format=json`

This will save your playlists and liked songs into the file "playlists.json".

## Reverse your playlists - Tab 2
As mentionned below, the original program adds the songs in the 'wrong' order. That's a feature I don't like, so I created a script to reverse them. It seems to be reliable, but if you find anything weird, please open an issue. It creates a backup of the original file just in case anyway.

## Import Your Liked Songs - Tab 3
#### Click the `import` button, and wait until it finished and switched to the next tab.

It will go through your Spotify liked songs, and like them on YTMusic.  It will display
the song from spotify and then the song that it found on YTMusic that it is liking.  I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify.  So far I haven't seen a single failure across a couple hundread songs, but more
esoteric titles it may have issues with.

## List Your Playlists - Tab 4

#### Click the `list` button, and wait until it finished and switched to the next tab.

This will list the playlists you have on both Spotify and YTMusic, so you can individually copy them.

## Copy Your Playlists - Tab 5

You can either copy **all** playlists, or do a more surgical copy of individual playlists.
Copying all playlists will use the name of the Spotify playlist as the destination playlist name on YTMusic.

#### To copy all the playlists click the `copy` button, and wait until it finished and switched to the next tab.

**NOTE**: This does not copy the Liked playlist (see above to do that).

## Copy specific Playlist - Tab 6

In the list output, find the "playlist id" (the first column) of the Spotify playlist and of the YTMusic playlist.
#### Then fill both input fields and click the `copy` button.


The copy playlist will take the name of the YTMusic playlist and will create the
playlist if it does not exist, if you start the YTMusic playlist with a "+":


Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.


## License

Creative Commons Zero v1.0 Universal

[//]: # ( vim: set tw=90 ts=4 sw=4 ai: )
