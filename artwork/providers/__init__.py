"""Album artwork providers."""

from .base import ArtworkProvider, ArtworkResult
from .musicbrainz import MusicBrainzProvider
from .lastfm import LastFMProvider
from .discogs import DiscogsProvider
from .itunes import ITunesProvider
from .google_images import GoogleImagesProvider

__all__ = [
    'ArtworkProvider',
    'ArtworkResult',
    'MusicBrainzProvider',
    'LastFMProvider',
    'DiscogsProvider',
    'ITunesProvider',
    'GoogleImagesProvider'
]
