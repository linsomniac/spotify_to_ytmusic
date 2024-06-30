#!/usr/bin/env python3

from . import cli
import sys
import inspect

def list_commands(module):
    # include only functions defined in e.g. 'cli' module
    commands = [name for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
    return commands

available_commands = list_commands(cli)

if len(sys.argv) < 2:
    print(f"usage: spotify2ytmusic [COMMAND] <ARGUMENTS>")
    print("Available commands:", ", ".join(available_commands))
    print("       For example, try 'spotify2ytmusic list_playlists'")
    sys.exit(1)

if sys.argv[1] not in available_commands:
    print(
        f"ERROR: Unknown command '{sys.argv[1]}', see https://github.com/linsomniac/spotify_to_ytmusic"
    )
    print("Available commands: ", ", ".join(available_commands))
    sys.exit(1)

fn = getattr(cli, sys.argv[1])
sys.argv = sys.argv[1:]
fn()
