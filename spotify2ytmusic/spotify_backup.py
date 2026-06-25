#!/usr/bin/env python3
#
# This file is licensed under the MIT license
# Original project: https://github.com/caseychu/spotify-backup

import base64
import codecs
import hashlib
import http.server
import json
import secrets
import sys
import time
import urllib.parse
import urllib.request
import webbrowser


class SpotifyAPI:
    """Class to interact with the Spotify API using an OAuth token."""

    BASE_URL = "https://api.spotify.com/v1/"
    _SERVER_PORT = 43019

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

        while response.get("next"):
            response = self.get(response["next"])
            items += response["items"]

        return items

    @staticmethod
    def authorize(client_id, scope):
        """Open browser for authorization and return SpotifyAPI instance."""

        redirect_uri = f"http://127.0.0.1:{SpotifyAPI._SERVER_PORT}/redirect"

        # PKCE
        code_verifier = secrets.token_urlsafe(64)

        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "scope": scope,
                "redirect_uri": redirect_uri,
                "code_challenge_method": "S256",
                "code_challenge": code_challenge,
            }
        )

        print("Open this link if the browser doesn't open automatically:\n" + auth_url)

        webbrowser.open(auth_url)

        server = SpotifyAPI._AuthorizationServer(
            "127.0.0.1",
            SpotifyAPI._SERVER_PORT,
        )

        try:
            while True:
                server.handle_request()
        except SpotifyAPI._Authorization as auth:
            code = auth.code

        print("Exchanging authorization code for access token...")

        token_request = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=urllib.parse.urlencode(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "code_verifier": code_verifier,
                }
            ).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        with urllib.request.urlopen(token_request) as response:
            token_response = json.load(codecs.getreader("utf-8")(response))

        return SpotifyAPI(token_response["access_token"])

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

    class _AuthorizationServer(http.server.HTTPServer):
        def __init__(self, host, port):
            super().__init__(
                (host, port),
                SpotifyAPI._AuthorizationHandler,
            )

        def handle_error(self, request, client_address):
            raise

    class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/redirect?"):
                self._handle_code()
            else:
                self.send_error(404)

        def _handle_code(self):
            query = urllib.parse.urlparse(self.path).query

            params = urllib.parse.parse_qs(query)

            if "code" not in params:
                self.send_error(
                    400,
                    "Missing authorization code",
                )
                return

            code = params["code"][0]

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html",
            )
            self.end_headers()

            self.wfile.write(
                b"""
                <html>
                <body>
                <h2>Authentication successful!</h2>
                You may now close this window.
                <script>window.close();</script>
                </body>
                </html>
                """
            )

            raise SpotifyAPI._Authorization(code)

        def log_message(self, format, *args):
            pass

    class _Authorization(Exception):
        def __init__(self, code):
            self.code = code


def fetch_user_data(spotify, dump):
    """Fetch playlists and liked songs."""

    playlists = []
    liked_albums = []

    if "liked" in dump:
        print("Loading liked albums and songs...")

        liked_tracks = spotify.list(
            "me/tracks",
            {"limit": 50},
        )

        liked_albums = spotify.list(
            "me/albums",
            {"limit": 50},
        )

        playlists.append(
            {
                "name": "Liked Songs",
                "tracks": liked_tracks,
            }
        )

    if "playlists" in dump:
        print("Loading playlists...")

        playlist_data = spotify.list(
            "me/playlists",
            {"limit": 50},
        )

        for playlist in playlist_data:
            print(f"Loading playlist: {playlist['name']}")

            playlist["tracks"] = spotify.list(
                playlist["tracks"]["href"],
                {"limit": 100},
            )

        playlists.extend(playlist_data)

    return playlists, liked_albums


def write_to_file(
    file,
    format,
    playlists,
    liked_albums,
):
    """Write fetched data to a file."""

    print(f"Writing to {file}...")

    with open(
        file,
        "w",
        encoding="utf-8",
    ) as f:
        if format == "json":
            json.dump(
                {
                    "playlists": playlists,
                    "albums": liked_albums,
                },
                f,
            )

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
                                    artist["name"]
                                    for artist in track["track"]["artists"]
                                ),
                                album=track["track"]["album"]["name"],
                                release_date=track["track"]["album"]["release_date"],
                            )
                        )

                f.write("\r\n")


def main(
    dump="playlists,liked",
    format="json",
    file="playlists.json",
    token="",
):
    print("Starting backup...")

    spotify = (
        SpotifyAPI(token)
        if token
        else SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope=(
                "playlist-read-private playlist-read-collaborative user-library-read"
            ),
        )
    )

    playlists, liked_albums = fetch_user_data(
        spotify,
        dump,
    )

    write_to_file(
        file,
        format,
        playlists,
        liked_albums,
    )

    print(f"Backup completed! Data written to {file}")


if __name__ == "__main__":
    main()
