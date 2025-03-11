#!/usr/bin/env python3

"""
Music Metadata Normalization and Matching

This module provides utilities for comparing and matching music tracks
between different streaming services (Spotify and YouTube Music) by normalizing metadata.

Features:
- ASCII conversion of international characters
- Metadata cleaning (removing version indicators, features, etc.)
- Smart text comparison with multiple matching strategies
- Track matching based on title, album, and artist information
"""

import re


def transliterate_text(text: str) -> str:
    """
    Convert non-ASCII characters to their ASCII equivalents.
    """
    # Character mapping dictionary for common accents and special characters
    replacements = {
        # Vowels with diacritics
        **{c: 'a' for c in 'áàâäãå'}, **{c: 'A' for c in 'ÁÀÂÄÃÅ'}, 
        **{c: 'e' for c in 'éèêë'}, **{c: 'E' for c in 'ÉÈÊË'},
        **{c: 'i' for c in 'íìîï'}, **{c: 'I' for c in 'ÍÌÎÏ'},
        **{c: 'o' for c in 'óòôöõø'}, **{c: 'O' for c in 'ÓÒÔÖÕØ'},
        **{c: 'u' for c in 'úùûü'}, **{c: 'U' for c in 'ÚÙÛÜ'},
        **{c: 'y' for c in 'ýÿ'}, **{c: 'Y' for c in 'ÝŸ'},
        # Special characters
        'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
        'ñ': 'n', 'Ñ': 'N', 'ç': 'c', 'Ç': 'C',
        'ß': 'ss', 'þ': 'th', 'Þ': 'TH',
    }
    
    return ''.join(replacements.get(char, char) for char in text)


def clean_metadata(metadata: str, metadata_type: str = "track") -> str:
    """
    Standardize and clean music metadata by removing variations and formatting.
    
    Args:
        metadata: Raw metadata text to clean
        metadata_type: Type of metadata ("track", "album", or "artist")
        
    Returns:
        Cleaned and standardized metadata string
    """
    # Convert to lowercase and transliterate international characters
    metadata = transliterate_text(metadata).lower()
    
    # Replace ampersands with "and" for consistency
    metadata = metadata.replace("&", "and")
    
    if metadata_type == "track":
        # Remove featuring artists sections
        metadata = re.sub(r"[\[(\{](?:feat|featuring|ft|with|prod|prod\.? by|produced by)\.? .*?[\]\)\}]", "", metadata)
        # Remove common track version identifiers (but not remix, as that would likely be a different track)
        metadata = re.sub(r"\b(?:deluxe|instrumental|bonus\strack|radio|video|edit|version|edition|single|mono|original|mix|lp|extended|remaster(?:ed)?|re-?edit)(?:\b|$)", "", metadata)
        # Remove anything after featuring artists indicators
        metadata = re.sub(r"\b(?:ft\.?|feat\.?|featuring|with|prod\.?(?:\s?by)?)\b.*$", "", metadata)
                
    elif metadata_type == "album":
        # Remove album edition/version indicators
        metadata = re.sub(r"\b(?:the|super|deluxe|special|anniversary|\d{2}th|extended|version|expanded|edition|re-?master(?:ed)?)(?:\b|$)", "", metadata)
        metadata = re.sub(r"\b(?:ep|lp|single|instrumentals?)(?:\b|$)", "", metadata)

    elif metadata_type == "artist":
        # Remove spaces for artist comparison
        metadata = re.sub(r"\bthe\s+", "", metadata)  # Remove "the " prefix
        metadata = re.sub(r"\s+", "", metadata)       # Remove all spaces
        
    # General cleaning patterns
    metadata = re.sub(r"(?<!\d)(?:17|18|19|20)\d{2}(?!\d)", "", metadata)  # Remove years
    metadata = re.sub(r"[.,\"`´’':;+*!\/\-\(\)\[\]\{\}]", "", metadata)  # Remove unwanted characters

    metadata = re.sub(r"\s+", " ", metadata).strip()  # Normalize whitespace

    return metadata.strip()


def clean_track_name(track_name: str) -> str:
    """
    Clean and standardize a track name.
    """
    return clean_metadata(track_name, "track")


def clean_album_name(album_name: str) -> str:
    """
    Clean and standardize an album name.
    """
    return clean_metadata(album_name, "album")


def clean_artist_name(artist_name: str) -> str:
    """
    Clean and standardize an artist name.
    """
    return clean_metadata(artist_name, "artist")

def levenshtein_distance(text1: str, text2: str) -> int:
    """
    Calculate the edit distance between two strings.
    
    This measures how many single-character changes (insertions, deletions, 
    or substitutions) are needed to transform one string into another.
        
    Returns:
        The number of edits needed to transform text1 into text2
    """
    if len(text1) < len(text2): 
        return levenshtein_distance(text2, text1)
    if not text2: 
        return len(text1)
    prev = list(range(len(text2) + 1))
    for i, ca in enumerate(text1):
        curr = [i + 1]
        for j, cb in enumerate(text2):
            curr.append(min(prev[j+1] + 1, curr[-1] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]

def text_similarity(text1: str, text2: str) -> bool:
    """
    Determine if two text strings should be considered similar/matching.
    
    Uses multiple text comparison strategies including:
    - Direct equality
    - Substring matching
    - Word reordering detection
    - Fuzzy matching (up to 2 character differences)
        
    Returns:
        True if texts are considered similar, False otherwise
    """
    text1 = text1.strip().lower()
    text2 = text2.strip().lower()
        
    # Length disparity check - different lengths suggest different content
    if len(text1) > 1.7 * len(text2) or len(text2) > 1.7 * len(text1):
        return False

    # Direct equality or substring matching
    if text1 == text2 or text1 in text2 or text2 in text1:
        return True

    # Word reordering check (for multi-word texts)
    text1_parts = text1.split()
    text2_parts = text2.split()
    if len(text1_parts) > 1 and len(text1_parts) == len(text2_parts):
        if set(text1_parts) == set(text2_parts):
            return True
    
    # Fuzzy matching with Levenshtein distance (checking for up to 2 spelling mistakes)
    if levenshtein_distance(text1, text2) <= 2:
        return True
    
    # Exact match after removing spaces
    if text1.replace(" ", "") == text2.replace(" ", ""):
        return True
    
    return False

def normalized_track_name_match(track1_name: str, track2_name: str) -> bool:
    """
    Compare two track names to determine if they refer to the same song.
    Handles variations in track names between music services.
        
    Returns:
        True if track names appear to match, False otherwise
    """
    cleaned_track1 = clean_track_name(track1_name)
    cleaned_track2 = clean_track_name(track2_name)

    if text_similarity(cleaned_track1, cleaned_track2):
        return True

    # Handle cases where artist name is embedded in track name with colon
    track1_parts = track1_name.split(":")
    track2_parts = track2_name.split(":")
    
    if len(track1_parts) == 2:
        cleaned_track1 = clean_track_name(track1_parts[1])
    if len(track2_parts) == 2:
        cleaned_track2 = clean_track_name(track2_parts[1])
        
    return text_similarity(cleaned_track1, cleaned_track2)


def normalized_album_name_match(album1_name: str, album2_name: str) -> bool:
    """
    Compare two album names to determine if they refer to the same album.
    Handles variations in album names between music services.
        
    Returns:
        True if album names appear to match, False otherwise
    """
    cleaned_album1 = clean_album_name(album1_name)
    cleaned_album2 = clean_album_name(album2_name)
    
    return text_similarity(cleaned_album1, cleaned_album2)


def normalized_artist_name_match(artist1_name: str, artist2_name: str) -> bool:
    """
    Compare two artist names to determine if they refer to the same artist.
    Handles variations in artist names between music services.
        
    Returns:
        True if artist names appear to match, False otherwise
    """
    # Youtube sometimes joins 2 artist names together in the artist field
    if artist1_name.strip().lower() in [name_part.strip() for name_part in re.split(r'[&,\/]|and|with', artist2_name.lower())] or \
       artist2_name.strip().lower() in [name_part.strip() for name_part in re.split(r'[&,\/]|and|with', artist1_name.lower())]:
        return True

    cleaned_artist1 = clean_artist_name(artist1_name)
    cleaned_artist2 = clean_artist_name(artist2_name)

    return text_similarity(cleaned_artist1, cleaned_artist2)


def normalized_track_match(spotify_track_name: str, spotify_album: str, spotify_artist: str, youtube_track: dict) -> bool:
    """
    Determine if a Spotify track matches a YouTube Music track.
    
    Uses multiple comparison strategies prioritizing track name and artist 
    matches while being more lenient with album names.
        
    Returns:
        True if the tracks likely match, False otherwise
    """
    youtube_track_name = youtube_track["title"]
    youtube_album = youtube_track["album"]["name"] if isinstance(youtube_track["album"], dict) else youtube_track["album"]
    youtube_artist = youtube_track["artists"][0]["name"]

    # Exact match for track and artist is a strong indicator (even if album is different)
    if spotify_track_name == youtube_track_name and spotify_artist == youtube_artist:
        return True

    # Check for instrumental/non-instrumental mismatch (reject these)
    spotify_is_instrumental = "instrumental" in f"{spotify_track_name} {spotify_album} {spotify_artist}".lower()
    youtube_is_instrumental = "instrumental" in f"{youtube_track_name} {youtube_album} {youtube_artist}".lower()
    if spotify_is_instrumental != youtube_is_instrumental:
        return False
    
    # Prioritize track name + artist match
    if normalized_track_name_match(spotify_track_name, youtube_track_name) and \
       normalized_artist_name_match(spotify_artist, youtube_artist):
        
        # Check album match but allow some flexibility if track and artist match well
        if normalized_album_name_match(spotify_album, youtube_album):
            return True
        
        # For exact track name matches, we can be more lenient with album mismatches
        cleaned_spotify_track = clean_track_name(spotify_track_name)
        cleaned_youtube_track = clean_track_name(youtube_track_name)
        if cleaned_spotify_track == cleaned_youtube_track:
            return True
    
    return False