"""Parser for extracting metadata from directory structure."""

from pathlib import Path
from typing import Optional

from models.track import TrackInfo, InfoSource
from .patterns import DIRECTORY_PATTERNS, YEAR_PATTERNS


class DirectoryParser:
    """Parses metadata from directory names and structure."""

    def parse(self, directory: Path) -> TrackInfo:
        """
        Parse a directory path to extract metadata.

        Analyzes both the directory name and parent directories.

        Args:
            directory: Path to the directory containing MP3 files

        Returns:
            TrackInfo with parsed data
        """
        info = TrackInfo(source=InfoSource.DIRECTORY, confidence=0.5)

        dir_name = directory.name
        parent_name = directory.parent.name if directory.parent != directory else None

        # Try to parse the directory name
        for pattern in DIRECTORY_PATTERNS:
            match = pattern.match(dir_name)
            if match:
                groups = match.groupdict()

                if 'artist' in groups and groups['artist']:
                    info.artist = self._clean_value(groups['artist'])

                if 'album' in groups and groups['album']:
                    info.album = self._clean_value(groups['album'])

                if 'year' in groups and groups['year']:
                    try:
                        info.year = int(groups['year'])
                    except ValueError:
                        pass

                # If we got artist and album, good confidence
                if info.artist and info.album:
                    info.confidence = 0.7
                    break

        # If no artist found, try parent directory
        if not info.artist and parent_name:
            # Parent is often the artist name
            # Only if it doesn't look like a generic folder
            generic_folders = {'music', 'mp3', 'downloads', 'audio', 'media',
                              'muusika', 'muusic', 'my music', 'users',
                              'documents', 'desktop', 'home'}

            if parent_name.lower() not in generic_folders:
                info.artist = self._clean_value(parent_name)
                info.confidence = 0.4  # Lower confidence for parent-derived artist

        # Try to extract year if not found
        if not info.year:
            info.year = self._extract_year(dir_name)

        # If we only have album (not artist), the dir name IS the album
        if not info.album and not info.artist:
            info.album = self._clean_value(dir_name)
            info.confidence = 0.3  # Low confidence for just album name

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

        # Remove year from value if it's at the end
        for pattern in YEAR_PATTERNS:
            value = pattern.sub('', value).strip()

        # Remove trailing/leading punctuation
        value = value.strip('-–—_.')

        return value

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text."""
        for pattern in YEAR_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    year = int(match.group(1))
                    # Validate year is reasonable
                    if 1900 <= year <= 2030:
                        return year
                except (ValueError, IndexError):
                    continue
        return None

    def analyze_structure(self, directory: Path) -> dict:
        """
        Analyze the directory structure for patterns.

        Returns information about how the music collection is organized.

        Returns:
            Dict with structure analysis:
            - pattern: detected pattern type
            - artist_level: directory level for artist
            - album_level: directory level for album
        """
        result = {
            'pattern': 'unknown',
            'artist_level': None,
            'album_level': None
        }

        # Count directory depth
        parts = list(directory.parts)

        # Common patterns:
        # /Music/Artist/Album/
        # /Music/Artist - Album/
        # /Music/Artist/Year - Album/

        if len(parts) >= 2:
            parent = directory.parent.name.lower()
            generic = {'music', 'mp3', 'downloads', 'audio'}

            if parent not in generic:
                # Parent is likely artist
                result['pattern'] = 'artist/album'
                result['artist_level'] = -2  # Second to last
                result['album_level'] = -1   # Last

        return result
