"""Parser for extracting metadata from MP3 filenames."""

from typing import Optional
import re

from models.track import TrackInfo, InfoSource
from .patterns import FILENAME_PATTERNS, TRACK_NUMBER_PATTERNS, CLEANUP_CHARS


class FilenameParser:
    """Parses metadata from MP3 filenames."""

    def parse(self, filename: str) -> TrackInfo:
        """
        Parse a filename to extract metadata.

        Args:
            filename: The MP3 filename (with extension)

        Returns:
            TrackInfo with parsed data
        """
        info = TrackInfo(source=InfoSource.FILENAME, confidence=0.6)

        # Try each pattern
        for pattern in FILENAME_PATTERNS:
            match = pattern.match(filename)
            if match:
                groups = match.groupdict()

                if 'artist' in groups and groups['artist']:
                    info.artist = self._clean_value(groups['artist'])

                if 'title' in groups and groups['title']:
                    info.title = self._clean_value(groups['title'])

                if 'album' in groups and groups['album']:
                    info.album = self._clean_value(groups['album'])

                if 'track' in groups and groups['track']:
                    try:
                        info.track_number = int(groups['track'])
                    except ValueError:
                        pass

                # Higher confidence for more specific patterns
                if info.artist and info.title:
                    info.confidence = 0.75
                if info.album:
                    info.confidence = 0.8

                break

        return info

    def _clean_value(self, value: str) -> str:
        """Clean up a parsed value."""
        if not value:
            return value

        # Strip whitespace
        value = value.strip()

        # Replace underscores with spaces
        value = value.replace('_', ' ')

        # Collapse multiple spaces
        value = ' '.join(value.split())

        # Fix common capitalization issues
        value = self._fix_capitalization(value)

        return value

    def _fix_capitalization(self, value: str) -> str:
        """Fix capitalization (title case with exceptions)."""
        # Common words that should stay lowercase
        lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
                          'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'}

        words = value.split()
        if not words:
            return value

        result = []
        for i, word in enumerate(words):
            # Always capitalize first word
            if i == 0:
                result.append(word.capitalize())
            # Keep all-caps words (likely acronyms)
            elif word.isupper() and len(word) <= 4:
                result.append(word)
            # Lowercase certain words (unless first)
            elif word.lower() in lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())

        return ' '.join(result)

    def extract_track_number(self, filename: str) -> Optional[int]:
        """
        Extract track number from filename.

        Args:
            filename: The filename to parse

        Returns:
            Track number if found, None otherwise
        """
        for pattern in TRACK_NUMBER_PATTERNS:
            match = pattern.search(filename)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def split_artist_title(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Split a string into artist and title parts.

        Handles various separators: " - ", " – ", " — ", etc.

        Args:
            text: String potentially containing "Artist - Title"

        Returns:
            Tuple of (artist, title) or (None, text) if no split found
        """
        # Various dash types
        separators = [' - ', ' – ', ' — ', ' _ ', ' / ']

        for sep in separators:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    artist = self._clean_value(parts[0])
                    title = self._clean_value(parts[1])
                    if artist and title:
                        return artist, title

        return None, text
