import os
import re

import ytmusicapi


def _headers_from_curl_bash(curl_text: str) -> str:
    """
    ytmusicapi.setup expects Firefox-style lines 'name: value'. Chrome's
    'Copy as cURL' uses -H 'name: value' and -b '...', which that parser
    does not understand. Convert cURL paste into the expected format.
    """
    lines: list[str] = []

    m = re.search(r"-b\s+'([^']*)'", curl_text)
    if m:
        lines.append(f"cookie: {m.group(1)}")
    else:
        m = re.search(r'-b\s+"((?:\\.|[^"\\])*)"', curl_text)
        if m:
            lines.append(f"cookie: {re.sub(r'\\(.)', r'\1', m.group(1))}")

    for m in re.finditer(r"-H\s+'([^']*)'", curl_text):
        part = m.group(1)
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        lines.append(f"{name.strip()}: {value.strip()}")

    for m in re.finditer(r'-H\s+"((?:\\.|[^"\\])*)"', curl_text):
        part = re.sub(r'\\(.)', r"\1", m.group(1))
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        lines.append(f"{name.strip()}: {value.strip()}")

    return "\n".join(lines)


def _normalize_headers_raw(raw: str) -> str:
    s = raw.strip()
    if s.lower().startswith("curl "):
        converted = _headers_from_curl_bash(raw)
        if not converted.strip():
            return raw
        return converted
    return raw


def setup_ytmusic_with_raw_headers(
    input_file="raw_headers.txt", credentials_file="oauth.json"
):
    """
    Loads raw headers from a file and sets up YTMusic connection using ytmusicapi.setup.

    Parameters:
        input_file (str): Path to the file containing raw headers.
        credentials_file (str): Path to save the configuration headers (credentials).

    Returns:
        str: Configuration headers string returned by ytmusicapi.setup.
    """
    # Check if the input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} does not exist.")

    # Read the raw headers from the file
    with open(input_file, "r") as file:
        headers_raw = _normalize_headers_raw(file.read())

    # Use ytmusicapi.setup to process headers and save the credentials
    config_headers = ytmusicapi.setup(
        filepath=credentials_file, headers_raw=headers_raw
    )
    print(f"Configuration headers saved to {credentials_file}")
    return config_headers


if __name__ == "__main__":
    try:
        # Specify file paths
        raw_headers_file = "raw_headers.txt"
        credentials_file = "oauth.json"

        # Set up YTMusic with raw headers
        print(f"Setting up YTMusic using headers from {raw_headers_file}...")
        setup_ytmusic_with_raw_headers(
            input_file=raw_headers_file, credentials_file=credentials_file
        )

        print("YTMusic setup completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
