# Claude Code Project Context

## Project Overview
MP3 tag editor desktop application with PySide6 GUI. Fetches album artwork from multiple online providers and writes ID3 tags to MP3 files.

## Architecture

### Core Components
- **core/analyzer.py** - Analyzes MP3 files, extracts existing tags
- **core/fingerprint.py** - Audio fingerprinting via AcoustID/Chromaprint
- **core/matcher.py** - Matches tracks to online databases, resolves conflicts
- **core/tagger.py** - Writes ID3 tags using mutagen

### Data Flow
1. User selects file/directory
2. `analyzer` extracts existing metadata
3. `parsers` extract info from filename/directory structure
4. `fingerprint` identifies track via audio fingerprint (optional)
5. `artwork/fetcher` queries providers for album art
6. `matcher` combines all sources, user resolves conflicts
7. `tagger` writes final tags to file

### Artwork Providers (priority order)
1. MusicBrainz - most reliable, free
2. iTunes - high quality images
3. Last.fm - good fallback
4. Discogs - requires API token
5. Google Images - last resort

### GUI Structure
- **main_window.py** - Main application window, handles file/directory selection
- **single_file_view.py** - Edit single MP3 file
- **directory_view.py** - Batch process directory
- **artwork_picker.py** - Choose between artwork options
- **conflict_dialog.py** - Resolve metadata conflicts
- **settings_dialog.py** - API keys, preferences

## Tech Stack
- **GUI**: PySide6 (Qt for Python)
- **Tags**: mutagen (ID3v2.4)
- **HTTP**: httpx (async capable)
- **Images**: Pillow
- **Cache**: diskcache

## Code Conventions
- Estonian language in UI strings and user-facing messages
- English in code (variable names, comments, docstrings)
- Type hints used throughout
- Dataclasses for models (Track, Album)
- Config stored in ~/.mp3_tag_editor/

## Known Limitations
- Only MP3 files supported (no FLAC, OGG, etc.)
- Chromaprint/fpcalc must be installed separately for fingerprinting
- Some providers require API keys for full functionality

## Common Tasks

### Adding a new artwork provider
1. Create new file in `artwork/providers/`
2. Inherit from `BaseProvider` in `base.py`
3. Implement `search(artist, album)` method
4. Register in `artwork/providers/__init__.py`
5. Add to fetcher priority list in `artwork/fetcher.py`

### Adding new filename pattern
1. Edit `parsers/patterns.py`
2. Add regex pattern to `FILENAME_PATTERNS` list
3. Test with various filename formats

## Testing
No tests yet. Would benefit from:
- Unit tests for parsers
- Mock tests for API providers
- Integration tests for tagger
