#!/usr/bin/env python3
#
#  This file is licensed under the MIT license
#  This file originates from https://github.com/caseychu/spotify-backup

import codecs
import base64
import hashlib
import http.client
import http.server
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


class SpotifyAPI:
    """Class to interact with the Spotify API using an OAuth token."""

    BASE_URL = "https://api.spotify.com/v1/"

    def __init__(self, auth):
        self._auth = auth

    def get(self, url, params={}, tries=3):
        """Fetch a resource from Spotify API."""
        url = self._construct_url(url, params)
        for _ in range(tries):
            try:
                req = self._create_request(url)
                return self._read_response(req)
            except Exception as err:
                print(f"Error fetching URL {url}: {err}")
                time.sleep(2)
        sys.exit("Failed to fetch data from Spotify API after retries.")

    def list(self, url, params={}):
        """Fetch paginated resources and return as a combined list."""
        response = self.get(url, params)
        items = response["items"]

        while response["next"]:
            response = self.get(response["next"])
            items += response["items"]
        return items

    @staticmethod
    def authorize(client_id, scope):
        """Open a browser for user authorization and return SpotifyAPI instance."""
        redirect_uri = f"http://127.0.0.1:{SpotifyAPI._SERVER_PORT}/redirect"
        code_verifier = SpotifyAPI._generate_code_verifier()
        code_challenge = SpotifyAPI._generate_code_challenge(code_verifier)
        url = SpotifyAPI._construct_auth_url(
            client_id,
            scope,
            redirect_uri,
            response_type="code",
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )
        print(f"Open this link if the browser doesn't open automatically: {url}")
        webbrowser.open(url)

        server = SpotifyAPI._AuthorizationServer(
            "127.0.0.1",
            SpotifyAPI._SERVER_PORT,
            client_id,
            redirect_uri,
            code_verifier,
        )
        try:
            while True:
                server.handle_request()
        except SpotifyAPI._Authorization as auth:
            return SpotifyAPI(auth.access_token)
        except SpotifyAPI._AuthorizationError as err:
            sys.exit(f"Authorization failed: {err.message}")

    @staticmethod
    def _construct_auth_url(
        client_id,
        scope,
        redirect_uri,
        response_type="code",
        code_challenge=None,
        code_challenge_method=None,
    ):
        params = {
            "response_type": response_type,
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
        if code_challenge_method:
            params["code_challenge_method"] = code_challenge_method
        return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            params
        )

    def _construct_url(self, url, params):
        """Construct a full API URL."""
        if not url.startswith(self.BASE_URL):
            url = self.BASE_URL + url
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        return url

    def _create_request(self, url):
        """Create an authenticated request."""
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self._auth}")
        return req

    def _read_response(self, req):
        """Read and parse the response."""
        with urllib.request.urlopen(req) as res:
            reader = codecs.getreader("utf-8")
            return json.load(reader(res))

    @staticmethod
    def _generate_code_verifier():
        return base64.urlsafe_b64encode(os.urandom(64)).decode("ascii").rstrip("=")

    @staticmethod
    def _generate_code_challenge(code_verifier):
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    _SERVER_PORT = 43019

    class _AuthorizationServer(http.server.HTTPServer):
        def __init__(self, host, port, client_id, redirect_uri, code_verifier):
            self.client_id = client_id
            self.redirect_uri = redirect_uri
            self.code_verifier = code_verifier
            super().__init__((host, port), SpotifyAPI._AuthorizationHandler)

        def handle_error(self, request, client_address):
            raise

    class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/redirect"):
                self._handle_code()
            elif self.path.startswith("/token?"):
                self._handle_token()
            else:
                self.send_error(404)

        def _handle_code(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if not code:
                error = params.get("error", ["missing_code"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"Authorization failed: {error}".encode("utf-8", "replace")
                )
                raise SpotifyAPI._AuthorizationError(error)
            access_token = self._exchange_code_for_token(code)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<script>close()</script>Thanks! You may now close this window."
            )
            raise SpotifyAPI._Authorization(access_token)

        def _handle_token(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            access_token = params.get("access_token", [None])[0]
            if not access_token:
                error = params.get("error", ["missing_access_token"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"Authorization failed: {error}".encode("utf-8", "replace")
                )
                raise SpotifyAPI._AuthorizationError(error)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<script>close()</script>Thanks! You may now close this window."
            )
            raise SpotifyAPI._Authorization(access_token)

        def _exchange_code_for_token(self, code):
            data = urllib.parse.urlencode(
                {
                    "client_id": self.server.client_id,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.server.redirect_uri,
                    "code_verifier": self.server.code_verifier,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://accounts.spotify.com/api/token",
                data=data,
                method="POST",
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            try:
                with urllib.request.urlopen(req) as res:
                    reader = codecs.getreader("utf-8")
                    payload = json.load(reader(res))
            except urllib.error.HTTPError as err:
                payload = err.read().decode("utf-8", "replace")
                raise SpotifyAPI._AuthorizationError(payload)
            access_token = payload.get("access_token")
            if not access_token:
                raise SpotifyAPI._AuthorizationError("missing_access_token")
            return access_token

        def log_message(self, format, *args):
            pass

    class _Authorization(Exception):
        def __init__(self, access_token):
            self.access_token = access_token

    class _AuthorizationError(Exception):
        def __init__(self, message):
            self.message = message


def fetch_user_data(spotify, dump):
    """Fetch playlists and liked songs based on the dump parameter."""
    playlists = []
    liked_albums = []

    if "liked" in dump:
        print("Loading liked albums and songs...")
        liked_tracks = spotify.list("me/tracks", {"limit": 50})
        liked_albums = spotify.list("me/albums", {"limit": 50})
        playlists.append({"name": "Liked Songs", "tracks": liked_tracks})

    if "playlists" in dump:
        print("Loading playlists...")
        playlist_data = spotify.list("me/playlists", {"limit": 50})
        for playlist in playlist_data:
            print(f"Loading playlist: {playlist['name']}")
            playlist["tracks"] = spotify.list(
                playlist["tracks"]["href"], {"limit": 100}
            )
        playlists.extend(playlist_data)

    return playlists, liked_albums


def write_to_file(file, format, playlists, liked_albums):
    """Write fetched data to a file in the specified format."""
    print(f"Writing to {file}...")
    with open(file, "w", encoding="utf-8") as f:
        if format == "json":
            json.dump({"playlists": playlists, "albums": liked_albums}, f)
        else:
            for playlist in playlists:
                f.write(playlist["name"] + "\r\n")
                for track in playlist["tracks"]:
                    if track["track"]:
                        f.write(
                            "{name}\t{artists}\t{album}\t{uri}\t{release_date}\r\n".format(
                                uri=track["track"]["uri"],
                                name=track["track"]["name"],
                                artists=", ".join(
                                    [
                                        artist["name"]
                                        for artist in track["track"]["artists"]
                                    ]
                                ),
                                album=track["track"]["album"]["name"],
                                release_date=track["track"]["album"]["release_date"],
                            )
                        )
                f.write("\r\n")


def main(dump="playlists,liked", format="json", file="playlists.json", token=""):
    print("Starting backup...")
    spotify = (
        SpotifyAPI(token)
        if token
        else SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope="playlist-read-private playlist-read-collaborative user-library-read",
        )
    )

    playlists, liked_albums = fetch_user_data(spotify, dump)
    write_to_file(file, format, playlists, liked_albums)
    print(f"Backup completed! Data written to {file}")


if __name__ == "__main__":
    main()
