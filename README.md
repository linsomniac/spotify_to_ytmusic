# Running:
```
brew install python
brew install python-tk
git clone https://github.com/CY83R-3X71NC710N/spotify_to_ytmusic.git && cd spotify_to_ytmusic
python3 -m venv path/to/venv
source path/to/venv/bin/activate
pip3 install ytmusicapi
ytmusicapi oauth
cd spotify2ytmusic && python3 spotify_backup.py playlists.json --dump=liked,playlists --format=json
mv playlists.json ..
cd .. && python3 ./reverse_playlist.py ./playlists.json -r
python3 -m spotify2ytmusic gui --track-sleep=3
```

# Avoiding Ban:

Run the terminal application to transfer all playlists with a time to sleep of 3 seconds --track-sleep=3
