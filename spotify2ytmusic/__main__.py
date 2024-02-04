#!/usr/bin/env python3

from . import cli
import sys

if len(sys.argv) < 2:
    print(f"usage: spotify2ytmusic [COMMAND] <ARGUMENTS>")
    print("       For example, try 'list_playlists'")
    sys.exit(1)

if not hasattr(cli, sys.argv[1]):
    print(
        f"ERROR: Unknown command, see https://github.com/linsomniac/spotify_to_ytmusic"
    )
    sys.exit(1)

fn = getattr(cli, sys.argv[1])
sys.argv = sys.argv[1:]
fn()
