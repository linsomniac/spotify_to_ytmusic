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
rm -rf log.txt
python -u -m spotify2ytmusic load_liked --track-sleep=3 --algo 0 2>&1 | tee -a log.txt && python -u -m spotify2ytmusic load_liked_albums --track-sleep=3 --algo 0 2>&1 | tee -a log.txt && python -u -m spotify2ytmusic copy_all_playlists --track-sleep=3 --algo 0 --privacy PRIVATE 2>&1 | tee -a log.txt
```

# Avoiding Ban:

Run the terminal application to transfer all playlists with a time to sleep of 3 seconds --track-sleep=3

# Connection Stability

Various retry functions were added to the backend to ensure that a faulty connection does not prevent songs from being transfered.
