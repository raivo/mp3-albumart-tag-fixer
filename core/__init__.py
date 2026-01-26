"""Core functionality for MP3 tag analysis and manipulation."""

from .tagger import MP3Tagger
from .analyzer import TrackAnalyzer
from .fingerprint import AudioFingerprinter
from .matcher import InfoMatcher

__all__ = ['MP3Tagger', 'TrackAnalyzer', 'AudioFingerprinter', 'InfoMatcher']
