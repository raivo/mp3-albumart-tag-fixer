"""MP3 tag reading and writing using mutagen."""

from pathlib import Path
from typing import Optional
import io

from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3, TIT2, TPE1, TALB, TDRC, TRCK, TCON, APIC,
    ID3NoHeaderError, error as ID3Error
)

from models.track import Track, TrackInfo, InfoSource


class MP3Tagger:
    """Handles reading and writing MP3 ID3 tags."""

    @staticmethod
    def read_tags(file_path: Path) -> tuple[TrackInfo, Optional[bytes], dict]:
        """
        Read tags from an MP3 file.

        Returns:
            Tuple of (TrackInfo, artwork_bytes, audio_properties)
        """
        info = TrackInfo(source=InfoSource.TAG)
        artwork = None
        audio_props = {}

        try:
            audio = MP3(file_path)

            # Get audio properties
            audio_props = {
                'duration_seconds': audio.info.length,
                'bitrate': audio.info.bitrate,
                'sample_rate': audio.info.sample_rate
            }

            # Get ID3 tags
            if audio.tags:
                tags = audio.tags

                # Title
                if 'TIT2' in tags:
                    info.title = str(tags['TIT2'])

                # Artist
                if 'TPE1' in tags:
                    info.artist = str(tags['TPE1'])

                # Album
                if 'TALB' in tags:
                    info.album = str(tags['TALB'])

                # Year
                if 'TDRC' in tags:
                    year_str = str(tags['TDRC'])
                    try:
                        info.year = int(year_str[:4]) if year_str else None
                    except (ValueError, IndexError):
                        pass

                # Track number
                if 'TRCK' in tags:
                    track_str = str(tags['TRCK'])
                    if '/' in track_str:
                        num, total = track_str.split('/')
                        info.track_number = int(num) if num else None
                        info.total_tracks = int(total) if total else None
                    else:
                        info.track_number = int(track_str) if track_str else None

                # Genre
                if 'TCON' in tags:
                    info.genre = str(tags['TCON'])

                # Artwork (APIC frame)
                for key in tags:
                    if key.startswith('APIC'):
                        apic = tags[key]
                        artwork = apic.data
                        break

        except ID3NoHeaderError:
            # File has no ID3 tags
            pass
        except Exception as e:
            raise RuntimeError(f"Error reading tags from {file_path}: {e}")

        return info, artwork, audio_props

    @staticmethod
    def write_tags(track: Track) -> None:
        """Write tags to an MP3 file."""
        if track.resolved_info is None and not track.new_artwork:
            return

        file_path = track.file_path
        info = track.resolved_info

        try:
            # Try to load existing tags or create new
            try:
                audio = MP3(file_path)
                if audio.tags is None:
                    audio.add_tags()
            except ID3NoHeaderError:
                audio = MP3(file_path)
                audio.add_tags()

            tags = audio.tags

            # Title
            if info and info.title:
                tags['TIT2'] = TIT2(encoding=3, text=info.title)

            # Artist
            if info and info.artist:
                tags['TPE1'] = TPE1(encoding=3, text=info.artist)

            # Album
            if info and info.album:
                tags['TALB'] = TALB(encoding=3, text=info.album)

            # Year
            if info and info.year:
                tags['TDRC'] = TDRC(encoding=3, text=str(info.year))

            # Track number
            if info and info.track_number:
                track_str = str(info.track_number)
                if info.total_tracks:
                    track_str = f"{info.track_number}/{info.total_tracks}"
                tags['TRCK'] = TRCK(encoding=3, text=track_str)

            # Genre
            if info and info.genre:
                tags['TCON'] = TCON(encoding=3, text=info.genre)

            # Artwork
            if track.new_artwork:
                # Remove existing artwork
                tags.delall('APIC')

                # Add new artwork
                tags['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=track.new_artwork
                )

            # Save
            audio.save()

        except Exception as e:
            track.error_message = f"Error writing tags: {e}"
            raise RuntimeError(f"Error writing tags to {file_path}: {e}")

    @staticmethod
    def remove_artwork(file_path: Path) -> None:
        """Remove artwork from an MP3 file."""
        try:
            audio = MP3(file_path)
            if audio.tags:
                audio.tags.delall('APIC')
                audio.save()
        except Exception as e:
            raise RuntimeError(f"Error removing artwork from {file_path}: {e}")

    @staticmethod
    def get_artwork(file_path: Path) -> Optional[bytes]:
        """Get artwork from an MP3 file."""
        try:
            audio = MP3(file_path)
            if audio.tags:
                for key in audio.tags:
                    if key.startswith('APIC'):
                        return audio.tags[key].data
        except Exception:
            pass
        return None

    @staticmethod
    def set_artwork(file_path: Path, artwork_data: bytes, mime_type: str = 'image/jpeg') -> None:
        """Set artwork for an MP3 file."""
        try:
            audio = MP3(file_path)
            if audio.tags is None:
                audio.add_tags()

            # Remove existing artwork
            audio.tags.delall('APIC')

            # Add new artwork
            audio.tags['APIC'] = APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # Cover (front)
                desc='Cover',
                data=artwork_data
            )

            audio.save()
        except Exception as e:
            raise RuntimeError(f"Error setting artwork for {file_path}: {e}")
