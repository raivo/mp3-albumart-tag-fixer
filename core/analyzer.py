"""Main analyzer that coordinates metadata gathering from all sources."""

from pathlib import Path
from typing import Optional

from models.track import Track, TrackInfo
from models.album import Album
from .tagger import MP3Tagger
from .fingerprint import AudioFingerprinter
from .matcher import InfoMatcher
from parsers import FilenameParser, DirectoryParser
from config import get_config, SUPPORTED_EXTENSIONS


class TrackAnalyzer:
    """Coordinates metadata analysis from all available sources."""

    def __init__(self):
        self.config = get_config()
        self.tagger = MP3Tagger()
        self.fingerprinter = AudioFingerprinter()
        self.matcher = InfoMatcher()
        self.filename_parser = FilenameParser()
        self.directory_parser = DirectoryParser()

    def analyze_file(self, file_path: Path) -> Track:
        """
        Analyze a single MP3 file from all sources.

        Returns a Track object with metadata from:
        - Existing tags
        - Filename parsing
        - Directory structure
        - Audio fingerprinting (if enabled)
        """
        track = Track(file_path=file_path)

        # 1. Read existing tags
        try:
            tag_info, artwork, audio_props = self.tagger.read_tags(file_path)
            track.tag_info = tag_info
            track.current_artwork = artwork
            track.duration_seconds = audio_props.get('duration_seconds')
            track.bitrate = audio_props.get('bitrate')
            track.sample_rate = audio_props.get('sample_rate')
        except Exception as e:
            track.error_message = f"Error reading tags: {e}"

        # 2. Parse filename
        try:
            track.filename_info = self.filename_parser.parse(file_path.name)
        except Exception as e:
            pass  # Filename parsing is optional

        # 3. Parse directory structure
        try:
            track.directory_info = self.directory_parser.parse(file_path.parent)
        except Exception as e:
            pass  # Directory parsing is optional

        # 4. Audio fingerprinting (if enabled and API key available)
        if self.config.use_fingerprinting and self.config.api.acoustid_api_key:
            try:
                track.acoustid_info = self.fingerprinter.lookup_by_fingerprint(file_path)
            except Exception as e:
                pass  # Fingerprinting is optional

        # 5. Auto-resolve if no conflicts
        if not self.matcher.needs_user_input(track):
            track.resolved_info = self.matcher.auto_resolve(track)

        track.is_processed = True
        return track

    def analyze_directory(self, directory: Path) -> Album:
        """
        Analyze all MP3 files in a directory.

        Returns an Album object containing all tracks.
        """
        album = Album(directory=directory)

        # Find all MP3 files
        mp3_files = []
        for ext in SUPPORTED_EXTENSIONS:
            mp3_files.extend(directory.glob(f"*{ext}"))

        # Sort by filename (usually gives correct track order)
        mp3_files.sort(key=lambda p: p.name.lower())

        # Analyze each file
        for file_path in mp3_files:
            track = self.analyze_file(file_path)
            album.add_track(track)

        return album

    def analyze_directory_recursive(self, directory: Path) -> list[Album]:
        """
        Recursively analyze all MP3 files in a directory tree.

        Each subdirectory with MP3 files is treated as a separate album.
        """
        albums = []

        # Check if current directory has MP3 files
        has_mp3s = any(directory.glob(f"*{ext}") for ext in SUPPORTED_EXTENSIONS)
        if has_mp3s:
            albums.append(self.analyze_directory(directory))

        # Recurse into subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                albums.extend(self.analyze_directory_recursive(subdir))

        return albums

    def get_conflicts(self, track: Track) -> dict:
        """Get all conflicts for a track in a user-friendly format."""
        conflicts = self.matcher.find_conflicts(track)
        result = {}

        for conflict in conflicts:
            result[conflict.field] = {
                'values': conflict.values,
                'suggested': self.matcher.suggest_resolution(conflict)
            }

        return result

    def resolve_conflict(self, track: Track, field: str, value: str) -> None:
        """Resolve a specific conflict with a user-selected value."""
        if track.resolved_info is None:
            track.resolved_info = self.matcher.auto_resolve(track)

        setattr(track.resolved_info, field, value)
        track.has_changes = True

    def apply_changes(self, track: Track) -> bool:
        """Apply resolved changes to the MP3 file."""
        if not track.has_changes:
            return False

        try:
            self.tagger.write_tags(track)
            track.has_changes = False
            return True
        except Exception as e:
            track.error_message = str(e)
            return False

    def preview_changes(self, track: Track) -> dict:
        """Get a preview of changes that would be applied."""
        changes = {}

        if track.resolved_info is not None:
            old_info = track.tag_info or TrackInfo()
            new_info = track.resolved_info

            for field in ['artist', 'album', 'title', 'year', 'track_number', 'genre']:
                old_val = getattr(old_info, field)
                new_val = getattr(new_info, field)

                if old_val != new_val:
                    changes[field] = {
                        'old': old_val,
                        'new': new_val
                    }

        # Check artwork regardless of resolved_info
        if track.new_artwork and track.new_artwork != track.current_artwork:
            changes['artwork'] = {
                'old': 'Exists' if track.current_artwork else 'None',
                'new': 'New image'
            }

        return changes
