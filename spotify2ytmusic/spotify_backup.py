#!/usr/bin/env python3

## A modified version of spotify-backup by 'caseychu' from https://github.com/caseychu/spotify-backup

import codecs, http.client, http.server, json, re, sys, time, urllib.error, urllib.parse, urllib.request, webbrowser


class SpotifyAPI:
    # Requires an OAuth token.
    def __init__(self, auth):
        self._auth = auth

    # Gets a resource from the Spotify API and returns the object.
    def get(self, url, params={}, tries=3):
        # Construct the correct URL.
        if not url.startswith("https://api.spotify.com/v1/"):
            url = "https://api.spotify.com/v1/" + url
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)

        # Try the sending off the request a specified number of times before giving up.
        for _ in range(tries):
            try:
                req = urllib.request.Request(url)
                req.add_header("Authorization", "Bearer " + self._auth)
                res = urllib.request.urlopen(req)
                reader = codecs.getreader("utf-8")
                return json.load(reader(res))
            except Exception as err:
                print("Couldn't load URL: {} ({})".format(url, err))
                time.sleep(2)
                print("Trying again...")
        sys.exit(1)

    # The Spotify API breaks long lists into multiple pages. This method automatically
    # fetches all pages and joins them, returning in a single list of objects.
    def list(self, url, params={}):
        last_log_time = time.time()
        response = self.get(url, params)
        items = response["items"]

        while response["next"]:
            if time.time() > last_log_time + 15:
                last_log_time = time.time()
                print(f"Loaded {len(items)}/{response['total']} items")

            response = self.get(response["next"])
            items += response["items"]
        return items

    # Pops open a browser window for a user to log in and authorize API access.
    @staticmethod
    def authorize(client_id, scope):
        url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            {
                "response_type": "token",
                "client_id": client_id,
                "scope": scope,
                "redirect_uri": "http://127.0.0.1:{}/redirect".format(
                    SpotifyAPI._SERVER_PORT
                ),
            }
        )
        print(f"Logging in (click if it doesn't open automatically): {url}")
        webbrowser.open(url)

        # Start a simple, local HTTP server to listen for the authorization token... (i.e. a hack).
        server = SpotifyAPI._AuthorizationServer("127.0.0.1", SpotifyAPI._SERVER_PORT)
        try:
            while True:
                server.handle_request()
        except SpotifyAPI._Authorization as auth:
            return SpotifyAPI(auth.access_token)

    # The port that the local server listens on. Don't change this,
    # as Spotify only will redirect to certain predefined URLs.
    _SERVER_PORT = 43019

    class _AuthorizationServer(http.server.HTTPServer):
        def __init__(self, host, port):
            http.server.HTTPServer.__init__(
                self, (host, port), SpotifyAPI._AuthorizationHandler
            )

        # Disable the default error handling.
        def handle_error(self, request, client_address):
            raise

    class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # The Spotify API has redirected here, but access_token is hidden in the URL fragment.
            # Read it using JavaScript and send it to /token as an actual query string...
            if self.path.startswith("/redirect"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b'<script>location.replace("token?" + location.hash.slice(1));</script>'
                )

            # Read access_token and use an exception to kill the server listening...
            elif self.path.startswith("/token?"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<script>close()</script>Thanks! You may now close this window."
                )

                access_token = re.search("access_token=([^&]*)", self.path).group(1)
                print(f"Received access token from Spotify: {access_token}")
                raise SpotifyAPI._Authorization(access_token)

            else:
                self.send_error(404)

        # Disable the default logging.
        def log_message(self, format, *args):
            pass

    class _Authorization(Exception):
        def __init__(self, access_token):
            self.access_token = access_token


def main(dump="playlists,liked", format="json", file="playlists.json", token=""):
    print("Starting backup...")
    # If they didn't give a filename, then just prompt them. (They probably just double-clicked.)
    while file == "":
        file = input("Enter a file name (e.g. playlists.txt): ")
        format = file.split(".")[-1]

    # Log into the Spotify API.
    if token != "":
        spotify = SpotifyAPI(token)
    else:
        spotify = SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope="playlist-read-private playlist-read-collaborative user-library-read",
        )

    # Get the ID of the logged in user.
    print("Loading user info...")
    me = spotify.get("me")
    print("Logged in as {display_name} ({id})".format(**me))

    playlists = []
    liked_albums = []

    # List liked albums and songs
    if "liked" in dump:
        print("Loading liked albums and songs...")
        liked_tracks = spotify.list(
            "users/{user_id}/tracks".format(user_id=me["id"]), {"limit": 50}
        )
        liked_albums = spotify.list("me/albums", {"limit": 50})
        playlists += [{"name": "Liked Songs", "tracks": liked_tracks}]

    # List all playlists and the tracks in each playlist
    if "playlists" in dump:
        print("Loading playlists...")
        playlist_data = spotify.list(
            "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
        )
        print(f"Found {len(playlist_data)} playlists")

        # List all tracks in each playlist
        for playlist in playlist_data:
            print("Loading playlist: {name} ({tracks[total]} songs)".format(**playlist))
            playlist["tracks"] = spotify.list(
                playlist["tracks"]["href"], {"limit": 100}
            )
        playlists += playlist_data

    # Write the file.
    print("Writing files...")
    with open(file, "w", encoding="utf-8") as f:
        # JSON file.
        if format == "json":
            json.dump({"playlists": playlists, "albums": liked_albums}, f)

        # Tab-separated file.
        else:
            f.write("Playlists: \r\n\r\n")
            for playlist in playlists:
                f.write(playlist["name"] + "\r\n")
                for track in playlist["tracks"]:
                    if track["track"] is None:
                        continue
                    f.write(
                        "{name}\t{artists}\t{album}\t{uri}\t{release_date}\r\n".format(
                            uri=track["track"]["uri"],
                            name=track["track"]["name"],
                            artists=", ".join(
                                [artist["name"] for artist in track["track"]["artists"]]
                            ),
                            album=track["track"]["album"]["name"],
                            release_date=track["track"]["album"]["release_date"],
                        )
                    )
                f.write("\r\n")
            if len(liked_albums) > 0:
                f.write("Liked Albums: \r\n\r\n")
                for album in liked_albums:
                    uri = album["album"]["uri"]
                    name = album["album"]["name"]
                    artists = ", ".join(
                        [artist["name"] for artist in album["album"]["artists"]]
                    )
                    release_date = album["album"]["release_date"]
                    album = f"{artists} - {name}"

                    f.write(f"{name}\t{artists}\t-\t{uri}\t{release_date}\r\n")

    print("Wrote file: " + file)


if __name__ == "__main__":
    main()
