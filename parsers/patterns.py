"""Regex patterns for parsing filenames and directories."""

import re

# Common filename patterns (ordered by specificity)
FILENAME_PATTERNS = [
    # "01 - Artist - Title.mp3" or "01. Artist - Title.mp3"
    re.compile(
        r'^(?P<track>\d{1,3})[\s\-\.]+(?P<artist>[^-]+)\s*-\s*(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),

    # "Artist - Album - 01 - Title.mp3"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<album>[^-]+)\s*-\s*(?P<track>\d{1,3})\s*-\s*(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),

    # "Artist - Album - Title.mp3"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<album>[^-]+)\s*-\s*(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),

    # "Artist - Title.mp3"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),

    # "01 Title.mp3" or "01. Title.mp3"
    re.compile(
        r'^(?P<track>\d{1,3})[\s\.\-]+(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),

    # "Title.mp3" (fallback - just title)
    re.compile(
        r'^(?P<title>.+?)\.mp3$',
        re.IGNORECASE
    ),
]

# Directory patterns for album info
DIRECTORY_PATTERNS = [
    # "Artist - Album (Year)"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<album>.+?)\s*\((?P<year>\d{4})\)$'
    ),

    # "Artist - Album [Year]"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<album>.+?)\s*\[(?P<year>\d{4})\]$'
    ),

    # "Artist - Album"
    re.compile(
        r'^(?P<artist>[^-]+)\s*-\s*(?P<album>.+)$'
    ),

    # "[Year] Artist - Album"
    re.compile(
        r'^\[(?P<year>\d{4})\]\s*(?P<artist>[^-]+)\s*-\s*(?P<album>.+)$'
    ),

    # "(Year) Artist - Album"
    re.compile(
        r'^\((?P<year>\d{4})\)\s*(?P<artist>[^-]+)\s*-\s*(?P<album>.+)$'
    ),

    # "Year - Artist - Album"
    re.compile(
        r'^(?P<year>\d{4})\s*-\s*(?P<artist>[^-]+)\s*-\s*(?P<album>.+)$'
    ),

    # Just album name (when parent is artist)
    re.compile(
        r'^(?P<album>.+)$'
    ),
]

# Parent directory patterns (for artist name)
PARENT_DIRECTORY_PATTERNS = [
    # Just artist name
    re.compile(
        r'^(?P<artist>.+)$'
    ),
]

# Year extraction patterns (standalone)
YEAR_PATTERNS = [
    re.compile(r'\((\d{4})\)'),      # (2020)
    re.compile(r'\[(\d{4})\]'),      # [2020]
    re.compile(r'^(\d{4})\s*-'),     # 2020 - ...
    re.compile(r'-\s*(\d{4})$'),     # ... - 2020
    re.compile(r'\b(19\d{2}|20[0-2]\d)\b'),  # Any year 1900-2029
]

# Track number patterns
TRACK_NUMBER_PATTERNS = [
    re.compile(r'^(\d{1,3})[\s\.\-]'),   # "01 ", "01. ", "01-"
    re.compile(r'^\[(\d{1,3})\]'),        # "[01]"
    re.compile(r'^\((\d{1,3})\)'),        # "(01)"
]

# Common words to remove from artist/album names
NOISE_WORDS = [
    'flac', 'mp3', 'wav', 'aac', 'ogg',
    '320kbps', '192kbps', '256kbps', 'v0', 'v2',
    'web', 'cd', 'vinyl', 'lp', 'ep',
    'remastered', 'deluxe', 'edition',
]

# Characters to clean from parsed values
CLEANUP_CHARS = ['_', '  ']
