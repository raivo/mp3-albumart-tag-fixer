"""Logic for matching and resolving metadata from multiple sources."""

from typing import Optional
from dataclasses import dataclass

from models.track import Track, TrackInfo, InfoSource


@dataclass
class Conflict:
    """Represents a conflict between metadata sources."""
    field: str  # artist, album, title, year
    values: dict[InfoSource, str]  # source -> value


class InfoMatcher:
    """Matches and resolves metadata from multiple sources."""

    def __init__(self):
        # Priority order for automatic resolution (highest first)
        self.source_priority = [
            InfoSource.ACOUSTID,      # Fingerprint is most reliable
            InfoSource.MUSICBRAINZ,   # Database lookup
            InfoSource.TAG,           # Existing tags
            InfoSource.FILENAME,      # Parsed from filename
            InfoSource.DIRECTORY,     # Parsed from directory
        ]

    def find_conflicts(self, track: Track) -> list[Conflict]:
        """Find all conflicting values across sources for a track."""
        conflicts = []

        for field in ['artist', 'album', 'title', 'year']:
            values = {}

            for source, info in track.get_all_info_sources():
                value = getattr(info, field)
                if value is not None:
                    # Normalize for comparison
                    normalized = self._normalize(str(value))
                    # Group by normalized value to find actual conflicts
                    values[source] = (value, normalized)

            # Check if there are different normalized values
            if values:
                normalized_values = set(v[1] for v in values.values())
                if len(normalized_values) > 1:
                    # Real conflict - different values
                    conflict = Conflict(
                        field=field,
                        values={src: val[0] for src, val in values.items()}
                    )
                    conflicts.append(conflict)

        return conflicts

    def _normalize(self, value: str) -> str:
        """Normalize a string for comparison."""
        # Lowercase, strip whitespace, remove common variations
        normalized = value.lower().strip()

        # Remove common prefixes/suffixes
        for prefix in ['the ', 'a ']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]

        # Remove special characters for comparison
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())  # Normalize whitespace

        return normalized

    def auto_resolve(self, track: Track) -> TrackInfo:
        """
        Automatically resolve metadata using source priority.

        Returns the best available metadata without user intervention.
        """
        resolved = TrackInfo(source=InfoSource.USER)

        for field in ['artist', 'album', 'title', 'year', 'track_number',
                      'total_tracks', 'genre', 'musicbrainz_artist_id',
                      'musicbrainz_album_id', 'musicbrainz_recording_id']:

            best_value = None
            best_confidence = 0.0

            for source in self.source_priority:
                info = self._get_info_by_source(track, source)
                if info:
                    value = getattr(info, field)
                    if value is not None:
                        # Use confidence-weighted priority
                        effective_confidence = info.confidence * (
                            1.0 - 0.1 * self.source_priority.index(source)
                        )
                        if effective_confidence > best_confidence:
                            best_value = value
                            best_confidence = effective_confidence

            if best_value is not None:
                setattr(resolved, field, best_value)

        return resolved

    def _get_info_by_source(self, track: Track, source: InfoSource) -> Optional[TrackInfo]:
        """Get TrackInfo from track by source type."""
        if source == InfoSource.TAG:
            return track.tag_info
        elif source == InfoSource.FILENAME:
            return track.filename_info
        elif source == InfoSource.DIRECTORY:
            return track.directory_info
        elif source in (InfoSource.ACOUSTID, InfoSource.MUSICBRAINZ):
            return track.acoustid_info
        return None

    def merge_all_sources(self, track: Track) -> TrackInfo:
        """
        Merge all available sources, filling in gaps.

        Uses priority order but accepts any available value for missing fields.
        """
        resolved = TrackInfo(source=InfoSource.USER)

        # Start with auto-resolve for priority-based values
        resolved = self.auto_resolve(track)

        # Fill in any remaining gaps from any source
        for field in ['artist', 'album', 'title', 'year', 'track_number',
                      'total_tracks', 'genre']:
            if getattr(resolved, field) is None:
                # Try all sources for missing values
                for source, info in track.get_all_info_sources():
                    value = getattr(info, field)
                    if value is not None:
                        setattr(resolved, field, value)
                        break

        return resolved

    def suggest_resolution(self, conflict: Conflict) -> tuple[InfoSource, str]:
        """
        Suggest the best resolution for a conflict.

        Returns (source, value) tuple with the recommended choice.
        """
        # Use priority order
        for source in self.source_priority:
            if source in conflict.values:
                return source, conflict.values[source]

        # Fallback to first available
        source = list(conflict.values.keys())[0]
        return source, conflict.values[source]

    def calculate_completeness(self, info: TrackInfo) -> float:
        """
        Calculate how complete the metadata is (0.0 to 1.0).

        Essential fields are weighted more heavily.
        """
        weights = {
            'artist': 0.25,
            'title': 0.25,
            'album': 0.20,
            'year': 0.15,
            'track_number': 0.10,
            'genre': 0.05
        }

        score = 0.0
        for field, weight in weights.items():
            if getattr(info, field) is not None:
                score += weight

        return score

    def needs_user_input(self, track: Track) -> bool:
        """Check if the track has conflicts that need user resolution."""
        conflicts = self.find_conflicts(track)
        return len(conflicts) > 0
