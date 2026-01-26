"""Audio fingerprinting using AcoustID/Chromaprint."""

from pathlib import Path
from typing import Optional
import subprocess
import json

import acoustid
import musicbrainzngs

from models.track import TrackInfo, InfoSource
from config import (
    get_config, MUSICBRAINZ_APP_NAME,
    MUSICBRAINZ_APP_VERSION, MUSICBRAINZ_CONTACT
)


# Initialize MusicBrainz client
musicbrainzngs.set_useragent(
    MUSICBRAINZ_APP_NAME,
    MUSICBRAINZ_APP_VERSION,
    MUSICBRAINZ_CONTACT
)


class AudioFingerprinter:
    """Handles audio fingerprinting and MusicBrainz lookups."""

    def __init__(self):
        self.config = get_config()

    def get_fingerprint(self, file_path: Path) -> Optional[tuple[float, str]]:
        """
        Get audio fingerprint for a file.

        Returns:
            Tuple of (duration, fingerprint) or None if failed
        """
        try:
            # Use acoustid library to get fingerprint
            duration, fingerprint = acoustid.fingerprint_file(str(file_path))
            return duration, fingerprint
        except acoustid.FingerprintGenerationError as e:
            print(f"Error generating fingerprint for {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fingerprinting {file_path}: {e}")
            return None

    def lookup_by_fingerprint(self, file_path: Path) -> Optional[TrackInfo]:
        """
        Look up track info using audio fingerprint.

        Returns:
            TrackInfo with data from MusicBrainz or None if not found
        """
        api_key = self.config.api.acoustid_api_key
        if not api_key:
            return None

        try:
            # Use acoustid to match
            results = acoustid.match(
                api_key,
                str(file_path),
                meta='recordings releases'
            )

            for score, recording_id, title, artist in results:
                if score < 0.5:  # Skip low confidence matches
                    continue

                info = TrackInfo(
                    source=InfoSource.ACOUSTID,
                    confidence=score
                )
                info.title = title
                info.artist = artist
                info.musicbrainz_recording_id = recording_id

                # Try to get more info from MusicBrainz
                mb_info = self._get_musicbrainz_info(recording_id)
                if mb_info:
                    info = info.merge_with(mb_info, prefer_other=True)

                return info

        except acoustid.NoBackendError:
            print("Chromaprint/fpcalc not found. Please install chromaprint.")
        except acoustid.WebServiceError as e:
            print(f"AcoustID web service error: {e}")
        except Exception as e:
            print(f"Error during AcoustID lookup: {e}")

        return None

    def _get_musicbrainz_info(self, recording_id: str) -> Optional[TrackInfo]:
        """Get detailed info from MusicBrainz for a recording."""
        try:
            result = musicbrainzngs.get_recording_by_id(
                recording_id,
                includes=['artists', 'releases', 'release-groups']
            )

            recording = result.get('recording', {})
            info = TrackInfo(source=InfoSource.MUSICBRAINZ)

            info.title = recording.get('title')
            info.musicbrainz_recording_id = recording_id

            # Get artist
            artist_credit = recording.get('artist-credit', [])
            if artist_credit:
                artists = []
                for credit in artist_credit:
                    if isinstance(credit, dict) and 'artist' in credit:
                        artists.append(credit['artist'].get('name', ''))
                        if not info.musicbrainz_artist_id:
                            info.musicbrainz_artist_id = credit['artist'].get('id')
                info.artist = ''.join(str(c) if isinstance(c, str) else c.get('artist', {}).get('name', '') + c.get('joinphrase', '') for c in artist_credit).strip()

            # Get release info (album)
            releases = recording.get('release-list', [])
            if releases:
                release = releases[0]  # Take first release
                info.album = release.get('title')
                info.musicbrainz_album_id = release.get('id')

                # Get year from release date
                date = release.get('date', '')
                if date:
                    try:
                        info.year = int(date[:4])
                    except (ValueError, IndexError):
                        pass

                # Get track number
                medium_list = release.get('medium-list', [])
                if medium_list:
                    track_list = medium_list[0].get('track-list', [])
                    for track in track_list:
                        if track.get('recording', {}).get('id') == recording_id:
                            try:
                                info.track_number = int(track.get('number', 0))
                            except ValueError:
                                pass
                            break

            return info

        except musicbrainzngs.WebServiceError as e:
            print(f"MusicBrainz error: {e}")
        except Exception as e:
            print(f"Error fetching MusicBrainz info: {e}")

        return None

    def search_musicbrainz(self, artist: str = None, album: str = None,
                           title: str = None) -> list[TrackInfo]:
        """
        Search MusicBrainz by metadata.

        Returns:
            List of matching TrackInfo objects
        """
        results = []

        try:
            if title and artist:
                # Search for recordings
                query = f'recording:"{title}" AND artist:"{artist}"'
                if album:
                    query += f' AND release:"{album}"'

                search_result = musicbrainzngs.search_recordings(
                    query=query,
                    limit=5
                )

                for recording in search_result.get('recording-list', []):
                    info = TrackInfo(source=InfoSource.MUSICBRAINZ)
                    info.title = recording.get('title')
                    info.musicbrainz_recording_id = recording.get('id')

                    # Get artist
                    artist_credit = recording.get('artist-credit', [])
                    if artist_credit and isinstance(artist_credit[0], dict):
                        info.artist = artist_credit[0].get('artist', {}).get('name')

                    # Get release info
                    releases = recording.get('release-list', [])
                    if releases:
                        info.album = releases[0].get('title')

                    # Calculate confidence based on match quality
                    score = recording.get('ext:score', 0)
                    info.confidence = float(score) / 100.0

                    results.append(info)

            elif album and artist:
                # Search for releases
                query = f'release:"{album}" AND artist:"{artist}"'
                search_result = musicbrainzngs.search_releases(
                    query=query,
                    limit=5
                )

                for release in search_result.get('release-list', []):
                    info = TrackInfo(source=InfoSource.MUSICBRAINZ)
                    info.album = release.get('title')
                    info.musicbrainz_album_id = release.get('id')

                    # Get artist
                    artist_credit = release.get('artist-credit', [])
                    if artist_credit and isinstance(artist_credit[0], dict):
                        info.artist = artist_credit[0].get('artist', {}).get('name')

                    # Get year
                    date = release.get('date', '')
                    if date:
                        try:
                            info.year = int(date[:4])
                        except (ValueError, IndexError):
                            pass

                    score = release.get('ext:score', 0)
                    info.confidence = float(score) / 100.0

                    results.append(info)

        except musicbrainzngs.WebServiceError as e:
            print(f"MusicBrainz search error: {e}")
        except Exception as e:
            print(f"Error searching MusicBrainz: {e}")

        return results
