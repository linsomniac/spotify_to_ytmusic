import cli


yt = cli.get_ytmusic()
ret = cli.lookup_song(yt, "Get Lucky (Radio Edit) [feat. Pharrell Williams and Nile Roger]", "Daft Punk", "Get Lucky (Radio Edit) [feat. Pharrell Williams and Nile Roger]")
print(ret)