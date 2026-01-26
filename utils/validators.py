"""Validation functions for metadata."""

import re
from typing import Optional


def validate_year(value) -> Optional[int]:
    """
    Validate and normalize a year value.

    Args:
        value: Year as int, string, or None

    Returns:
        Valid year as int, or None if invalid
    """
    if value is None:
        return None

    try:
        year = int(value)

        # Validate range
        if 1900 <= year <= 2030:
            return year

        return None

    except (ValueError, TypeError):
        # Try to extract year from string
        if isinstance(value, str):
            match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', value)
            if match:
                return int(match.group(1))

        return None


def validate_artist(value: str) -> Optional[str]:
    """
    Validate and clean an artist name.

    Args:
        value: Artist name

    Returns:
        Cleaned artist name or None if invalid
    """
    if not value:
        return None

    # Clean up whitespace
    value = ' '.join(value.split())

    # Remove common invalid values
    invalid_values = {
        'unknown', 'unknown artist', 'various', 'various artists',
        'va', 'n/a', 'none', 'artist', 'track', 'audio',
        'tundmatu', 'tundmatu artist', 'erinevad'
    }

    if value.lower() in invalid_values:
        return None

    # Minimum length
    if len(value) < 2:
        return None

    return value


def validate_album(value: str) -> Optional[str]:
    """
    Validate and clean an album name.

    Args:
        value: Album name

    Returns:
        Cleaned album name or None if invalid
    """
    if not value:
        return None

    # Clean up whitespace
    value = ' '.join(value.split())

    # Remove common invalid values
    invalid_values = {
        'unknown', 'unknown album', 'album', 'single', 'untitled',
        'n/a', 'none', 'audio', 'music',
        'tundmatu', 'tundmatu album'
    }

    if value.lower() in invalid_values:
        return None

    # Minimum length
    if len(value) < 1:
        return None

    return value


def validate_title(value: str) -> Optional[str]:
    """
    Validate and clean a track title.

    Args:
        value: Track title

    Returns:
        Cleaned title or None if invalid
    """
    if not value:
        return None

    # Clean up whitespace
    value = ' '.join(value.split())

    # Remove common invalid values
    invalid_values = {
        'unknown', 'track', 'audio', 'untitled',
        'n/a', 'none',
        'tundmatu'
    }

    if value.lower() in invalid_values:
        return None

    # Remove track number prefix if still present
    value = re.sub(r'^(\d{1,3})[\s\.\-]+', '', value)

    # Minimum length
    if len(value) < 1:
        return None

    return value


def validate_track_number(value) -> Optional[int]:
    """
    Validate a track number.

    Args:
        value: Track number as int, string, or None

    Returns:
        Valid track number as int, or None if invalid
    """
    if value is None:
        return None

    try:
        # Handle "3/12" format
        if isinstance(value, str) and '/' in value:
            value = value.split('/')[0]

        num = int(value)

        # Validate range (1-999 is reasonable)
        if 1 <= num <= 999:
            return num

        return None

    except (ValueError, TypeError):
        return None


def validate_genre(value: str) -> Optional[str]:
    """
    Validate and clean a genre.

    Args:
        value: Genre name

    Returns:
        Cleaned genre or None if invalid
    """
    if not value:
        return None

    # Clean up whitespace
    value = ' '.join(value.split())

    # Remove parenthetical ID3v1 genre IDs like "(17)"
    value = re.sub(r'^\(\d+\)\s*', '', value)

    # Common invalid values
    invalid_values = {
        'unknown', 'other', 'none', 'n/a', 'genre',
        'tundmatu', 'muu'
    }

    if value.lower() in invalid_values:
        return None

    # Minimum length
    if len(value) < 2:
        return None

    return value


def is_valid_filename(filename: str) -> bool:
    """
    Check if a filename is valid for an MP3 file.

    Args:
        filename: Filename to check

    Returns:
        True if valid, False otherwise
    """
    if not filename:
        return False

    # Check extension
    if not filename.lower().endswith('.mp3'):
        return False

    # Check for invalid characters (basic check)
    invalid_chars = '<>:"|?*'
    if any(c in filename for c in invalid_chars):
        return False

    return True
