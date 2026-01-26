"""Album data model representing a collection of tracks."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from .track import Track, TrackInfo


@dataclass
class Album:
    """Represents an album (collection of tracks)."""
    directory: Path
    tracks: list[Track] = field(default_factory=list)

    # Album-level metadata
    artist: Optional[str] = None
    album_name: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    total_tracks: Optional[int] = None

    # MusicBrainz IDs
    musicbrainz_album_id: Optional[str] = None
    musicbrainz_artist_id: Optional[str] = None

    # Artwork
    artwork: Optional[bytes] = None
    artwork_url: Optional[str] = None

    # Status
    is_compilation: bool = False
    is_processed: bool = False

    def add_track(self, track: Track) -> None:
        """Add a track to the album."""
        self.tracks.append(track)
        self._update_album_info()

    def _update_album_info(self) -> None:
        """Update album info based on tracks."""
        if not self.tracks:
            return

        # Try to determine album info from tracks
        artists = set()
        albums = set()
        years = set()

        for track in self.tracks:
            info = track.resolved_info or track.tag_info
            if info:
                if info.artist:
                    artists.add(info.artist)
                if info.album:
                    albums.add(info.album)
                if info.year:
                    years.add(info.year)

        # Set album info if consistent
        if len(artists) == 1:
            self.artist = artists.pop()
        elif len(artists) > 1:
            self.is_compilation = True
            self.artist = "Various Artists"

        if len(albums) == 1:
            self.album_name = albums.pop()

        if len(years) == 1:
            self.year = years.pop()

        self.total_tracks = len(self.tracks)

    def get_common_info(self) -> TrackInfo:
        """Get metadata that is common across all tracks."""
        from .track import InfoSource

        common = TrackInfo(source=InfoSource.TAG)

        if self.artist and not self.is_compilation:
            common.artist = self.artist
        if self.album_name:
            common.album = self.album_name
        if self.year:
            common.year = self.year
        if self.genre:
            common.genre = self.genre

        return common

    def apply_to_all_tracks(self, info: TrackInfo) -> None:
        """Apply metadata to all tracks in the album."""
        for track in self.tracks:
            if track.resolved_info is None:
                track.resolved_info = TrackInfo()

            # Apply album-level info but keep track-specific info
            if info.artist and not self.is_compilation:
                track.resolved_info.artist = info.artist
            if info.album:
                track.resolved_info.album = info.album
            if info.year:
                track.resolved_info.year = info.year
            if info.genre:
                track.resolved_info.genre = info.genre

            track.has_changes = True

    def set_artwork_for_all(self, artwork: bytes, url: Optional[str] = None) -> None:
        """Set the same artwork for all tracks."""
        self.artwork = artwork
        self.artwork_url = url

        for track in self.tracks:
            track.new_artwork = artwork
            track.artwork_url = url
            track.has_changes = True

    @property
    def track_count(self) -> int:
        """Get the number of tracks."""
        return len(self.tracks)

    def get_tracks_with_changes(self) -> list[Track]:
        """Get all tracks that have pending changes."""
        return [t for t in self.tracks if t.has_changes]

    def get_tracks_with_errors(self) -> list[Track]:
        """Get all tracks that have errors."""
        return [t for t in self.tracks if t.error_message]
