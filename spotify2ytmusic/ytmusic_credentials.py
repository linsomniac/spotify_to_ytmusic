import ytmusicapi

import os


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
        headers_raw = file.read()

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
