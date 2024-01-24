import cli


yt = cli.get_ytmusic()
# cli.copy_all_playlists()
ret = cli.lookup_song(yt, "Oui et non", "Nekfeu", "Les étoiles vagabondes : expansion")
print(ret)