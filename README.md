### Overview

This is a set of scripts for copying "liked" songs and playlists from Spotify to YTMusic. It provides a GUI (implemented by Yoween, formerly called spotify_to_ytmusic_gui).

---

### Preparation/Pre-Conditions

1. **Install Python and Git** (you may already have them installed).
2. **Uninstall the pip package from the original repository** (if you previously installed `linsomniac/spotify_to_ytmusic`):

   On Windows:

   ```bash
   python -m pip uninstall spotify2ytmusic
   ```

   On Linux or Mac:

   ```bash
   python3 -m pip uninstall spotify2ytmusic
   ```

---

### Setup Instructions

#### 1. Clone, Create a Virtual Environment, and Install Required Packages

Start by creating and activating a Python virtual environment to isolate dependencies.

```bash
git clone https://github.com/linsomniac/spotify_to_ytmusic.git
cd spotify_to_ytmusic
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install ytmusicapi tk
```

On Linux or Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ytmusicapi tk
```

---

#### 2. Generate YouTube Music Credentials

To use the YouTube Music API, you need to generate valid credentials. Follow these steps:

1. **Log in to YouTube Music**: Open YouTube Music in Firefox and ensure you are logged in.
2. **Open the Inspection Tool**: Press `F12` or right-click and select _Inspect_ to open the browser's inspection tool.
3. **Access the Network Tab**: Navigate to the Network tab and filter by `/browse`.
4. **Select a Request**: Click one of the requests under the filtered results and locate the _Request Headers_ section.
5. **Toggle RAW View**: Click the RAW toggle button to view the headers in raw format.
6. **Copy Headers**: Right-click, choose _Select All_, and copy the content.
7. **Paste into `raw_headers.txt`**: Open the `raw_headers.txt` file located in the main directory of this project and paste the copied content into it.

**Run the Script**:

Execute the following command to generate the credentials file:

On Windows:

```bash
python spotify2ytmusic/ytmusic_credentials.py
```

On Linux or Mac:

```bash
python3 spotify2ytmusic/ytmusic_credentials.py
```

**Important**: After running this script, the authentication file will be created.
When you launch the GUI in the next step, it will automatically detect this file and log in to YouTube Music without requiring manual input. You’ll see a log message confirming this:

```
File detected, auto login
```

The GUI will **ignore the 'Login to YT Music' tab** and jump straight to the 'Spotify Backup' tab.

---

#### 3. Use the GUI for Migration

Now you can use the graphical user interface (GUI) to migrate your playlists and liked songs to YouTube Music. Start the GUI with the following command:

On Windows:

```bash
python -m spotify2ytmusic gui
```

On Linux or Mac:

```bash
python3 -m spotify2ytmusic gui
```

---

### GUI Features

Once the GUI is running, you can:

- **Backup Your Spotify Playlists**: Save your playlists and liked songs into the file `playlists.json`.
- **Load Liked Songs**: Migrate your Spotify liked songs to YouTube Music.
- **List Playlists**: View your playlists and their details.
- **Copy All Playlists**: Migrate all Spotify playlists to YouTube Music.
- **Copy a Specific Playlist**: Select and migrate a specific Spotify playlist to YouTube Music.

---

### Import Your Liked Songs - Tab 3

#### Click the `import` button, and wait until it finished and switched to the next tab

It will go through your Spotify liked songs, and like them on YTMusic. It will display
the song from Spotify and then the song that it found on YTMusic that it is liking. I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify. So far I haven't seen a single failure across a couple hundred songs, but more
esoteric titles it may have issues with.

### List Your Playlists - Tab 4

#### Click the `list` button, and wait until it finished and switched to the next tab

This will list the playlists you have on both Spotify and YTMusic, so you can individually copy them.

### Copy Your Playlists - Tab 5

You can either copy **all** playlists, or do a more surgical copy of individual playlists.
Copying all playlists will use the name of the Spotify playlist as the destination playlist name on YTMusic.

#### To copy all the playlists click the `copy` button, and wait until it finished and switched to the next tab

**NOTE**: This does not copy the Liked playlist (see above to do that).

### Copy specific Playlist - Tab 6

In the list output, find the "playlist id" (the first column) of the Spotify playlist and of the YTMusic playlist.

#### Then fill both input fields and click the `copy` button

The copy playlist will take the name of the YTMusic playlist and will create the
playlist if it does not exist, if you start the YTMusic playlist with a "+":

Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.

## Command Line Usage

### Ways to Run

**NOTE**: There are two possible ways to run these commands, one is via standalone commands
if the application was installed, which takes the form of: `s2yt_load_liked`

If not fully installed, you can replace the "s2yt\_" with "python -m spotify2ytmusic", for
example: `s2yt_load_liked` becomes `python -j spotify2ytmusic load_liked`

### Login to YTMusic

See "Generate YouTube Music Credentials" above.

### Backup Your Spotify Playlists

Run `spotify2ytmusic/spotify-backup.py` and it will help you authorize access to your spotify account.

Run: `python3 spotify-backup.py playlists.json --dump=liked,playlists --format=json`

This will save your playlists and liked songs into the file "playlists.json".

### Import Your Liked Songs

Run: `s2yt_load_liked`

It will go through your Spotify liked songs, and like them on YTMusic. It will display
the song from spotify and then the song that it found on YTMusic that it is liking. I've
spot-checked my songs and it seems to be doing a good job of matching YTMusic songs with
Spotify. So far I haven't seen a single failure across a couple thousand songs, but more
esoteric titles it may have issues with.

### Import Your Liked Albums

Run: `s2yt_load_liked_albums`

Spotify stores liked albums outside of the "Liked Songs" playlist. This is the command to
load your liked albums into YTMusic liked songs.

### List Your Playlists

Run `s2yt_list_playlists`

This will list the playlists you have on both Spotify and YTMusic. You will need to
individually copy them.

### Copy Your Playlists

You can either copy **all** playlists, or do a more surgical copy of individual playlists.
Copying all playlists will use the name of the Spotify playlist as the destination
playlist name on YTMusic. To copy all playlists, run:

`s2yt_copy_all_playlists`

**NOTE**: This does not copy the Liked playlist (see above to do that).

In the list output above, find the "playlist id" (the first column) of the Spotify playlist,
and of the YTMusic playlist, and then run:

`s2yt_copy_playlist <SPOTIFY_PLAYLIST_ID> <YTMUSIC_PLAYLIST_ID>`

If you need to create a playlist, you can run:

`s2yt_create_playlist "<PLAYLIST_NAME>"`

_Or_ the copy playlist can take the name of the YTMusic playlist and will create the
playlist if it does not exist, if you start the YTMusic playlist with a "+":

`s2yt_copy_playlist <SPOTIFY_PLAYLIST_ID> +<YTMUSIC_PLAYLIST_NAME>`

For example:

`s2yt_copy_playlist SPOTIFY_PLAYLIST_ID "+Feeling Like a PUNK"`

Re-running "copy_playlist" or "load_liked" in the event that it fails should be safe, it
will not duplicate entries on the playlist.

### Searching for YTMusic Tracks

This is mostly for debugging, but there is a command to search for tracks in YTMusic:

## `s2yt_search --artist <ARTIST> --album <ALBUM> <TRACK_NAME>`

## Details About Search Algorithms

The function first searches for albums by the given artist name on YTMusic.

It then iterates over the first three album results and tries to find a track with
the exact same name as the given track name. If it finds a match, it returns the
track information.

If the function can't find the track in the albums, it then searches for songs by the
given track name and artist name.

Depending on the yt_search_algo parameter, it performs one of the following actions:

If yt_search_algo is 0, it simply returns the first song result.

If yt_search_algo is 1, it iterates over the song results and returns the first song
that matches the track name, artist name, and album name exactly. If it can't find a
match, it raises a ValueError.

If yt_search_algo is 2, it performs a fuzzy match. It removes everything in brackets
in the song title and checks for a match with the track name, artist name, and album
name. If it can't find a match, it then searches for videos with the track name and
artist name. If it still can't find a match, it raises a ValueError.

If the function can't find the track using any of the above methods, it raises a
ValueError.

## FAQ

- Does this run on mobile?

No, this runs on Linux/Windows/MacOS.

- How does the lookup algorithm work?

  Given the Spotify track information, it does a lookup for the album by the same artist
  on YTMusic, then looks at the first 3 hits looking for a track with exactly the same
  name. In the event that it can't find that exact track, it then does a search of songs
  for the track name by the same artist and simply returns the first hit.

  The idea is that finding the album and artist and then looking for the exact track match
  will be more likely to be accurate than searching for the song and artist and relying on
  the YTMusic algorithm to figure things out, especially for short tracks that might be
  have many contradictory hits like "Survival by Yes".

- My copy is failing with repeated "ERROR: (Retrying) Server returned HTTP 400: Bad
  Request".

  Try running with "--track-sleep=3" argument to do a 3 second sleep between tracks. This
  will take much longer, but may succeed where faster rates have failed.

## License

Creative Commons Zero v1.0 Universal

spotify-backup.py licensed under MIT License.
See <https://github.com/caseychu/spotify-backup> for more information.

[//]: # " vim: set tw=90 ts=4 sw=4 ai: "
