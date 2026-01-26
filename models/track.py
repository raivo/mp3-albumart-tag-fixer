"""Track data model representing an MP3 file and its metadata."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from enum import Enum


class InfoSource(Enum):
    """Source of metadata information."""
    TAG = "tag"              # From existing MP3 tags
    FILENAME = "filename"    # Parsed from filename
    DIRECTORY = "directory"  # Parsed from directory structure
    ACOUSTID = "acoustid"    # From audio fingerprinting
    MUSICBRAINZ = "musicbrainz"  # From MusicBrainz database
    USER = "user"            # Manually entered by user


@dataclass
class TrackInfo:
    """Metadata information with source tracking."""
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    genre: Optional[str] = None

    # Source tracking
    source: InfoSource = InfoSource.TAG
    confidence: float = 1.0  # 0.0 to 1.0

    # MusicBrainz IDs (if available)
    musicbrainz_artist_id: Optional[str] = None
    musicbrainz_album_id: Optional[str] = None
    musicbrainz_recording_id: Optional[str] = None

    def has_basic_info(self) -> bool:
        """Check if basic metadata is present."""
        return bool(self.artist and self.title)

    def has_album_info(self) -> bool:
        """Check if album information is present."""
        return bool(self.album)

    def merge_with(self, other: 'TrackInfo', prefer_other: bool = False) -> 'TrackInfo':
        """Merge with another TrackInfo, filling in missing values."""
        result = TrackInfo(source=self.source)

        for attr in ['artist', 'album', 'title', 'year', 'track_number',
                     'total_tracks', 'genre', 'musicbrainz_artist_id',
                     'musicbrainz_album_id', 'musicbrainz_recording_id']:
            self_val = getattr(self, attr)
            other_val = getattr(other, attr)

            if prefer_other and other_val is not None:
                setattr(result, attr, other_val)
            elif self_val is not None:
                setattr(result, attr, self_val)
            else:
                setattr(result, attr, other_val)

        return result


@dataclass
class Track:
    """Represents an MP3 file with all its metadata from various sources."""
    file_path: Path

    # Metadata from different sources
    tag_info: Optional[TrackInfo] = None
    filename_info: Optional[TrackInfo] = None
    directory_info: Optional[TrackInfo] = None
    acoustid_info: Optional[TrackInfo] = None

    # Final resolved metadata (after conflict resolution)
    resolved_info: Optional[TrackInfo] = None

    # Artwork
    current_artwork: Optional[bytes] = None
    new_artwork: Optional[bytes] = None
    artwork_url: Optional[str] = None

    # Status
    has_changes: bool = False
    is_processed: bool = False
    error_message: Optional[str] = None

    # Audio properties
    duration_seconds: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None

    @property
    def filename(self) -> str:
        """Get the filename without path."""
        return self.file_path.name

    @property
    def directory(self) -> Path:
        """Get the parent directory."""
        return self.file_path.parent

    def get_all_info_sources(self) -> list[tuple[InfoSource, TrackInfo]]:
        """Get all available info sources with their data."""
        sources = []
        if self.tag_info:
            sources.append((InfoSource.TAG, self.tag_info))
        if self.filename_info:
            sources.append((InfoSource.FILENAME, self.filename_info))
        if self.directory_info:
            sources.append((InfoSource.DIRECTORY, self.directory_info))
        if self.acoustid_info:
            sources.append((InfoSource.ACOUSTID, self.acoustid_info))
        return sources

    def has_conflicts(self) -> dict[str, list[tuple[InfoSource, str]]]:
        """Check for conflicting values across sources."""
        conflicts = {}

        for attr in ['artist', 'album', 'title', 'year']:
            values = []
            for source, info in self.get_all_info_sources():
                val = getattr(info, attr)
                if val is not None:
                    # Normalize for comparison
                    normalized = str(val).lower().strip() if attr != 'year' else val
                    values.append((source, val, normalized))

            # Check if there are different values
            if values:
                unique_normalized = set(v[2] for v in values)
                if len(unique_normalized) > 1:
                    conflicts[attr] = [(v[0], v[1]) for v in values]

        return conflicts
