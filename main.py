#!/usr/bin/env python3
"""
MP3 Tag Editor - Main entry point.

A desktop application for managing MP3 file metadata (tags) and album artwork.
Supports both single file and directory batch processing.

Features:
- Analyzes existing tags, filenames, and directory structure
- Audio fingerprinting via AcoustID/Chromaprint for accurate identification
- Fetches album artwork from multiple sources (MusicBrainz, Last.fm, Discogs, iTunes)
- Resolves conflicts between different metadata sources
- Preview changes before applying
- Estonian language interface

Usage:
    python main.py              # Launch the GUI application
    python main.py --help       # Show help
    python main.py --version    # Show version

Requirements:
    - Python 3.10+
    - PySide6 for GUI
    - mutagen for MP3 tag handling
    - pyacoustid for audio fingerprinting (requires fpcalc)
    - httpx for API requests
    - Pillow for image processing
    - diskcache for caching

Author: Your Name
License: MIT
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def check_dependencies():
    """Check that all required dependencies are installed."""
    missing = []

    try:
        import PySide6
    except ImportError:
        missing.append("PySide6")

    try:
        import mutagen
    except ImportError:
        missing.append("mutagen")

    try:
        import httpx
    except ImportError:
        missing.append("httpx")

    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")

    try:
        import diskcache
    except ImportError:
        missing.append("diskcache")

    try:
        import musicbrainzngs
    except ImportError:
        missing.append("musicbrainzngs")

    if missing:
        print("Puuduvad sõltuvused:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstalli puuduvad sõltuvused:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def check_chromaprint():
    """Check if Chromaprint/fpcalc is available for audio fingerprinting."""
    import shutil

    fpcalc_path = shutil.which('fpcalc')
    if not fpcalc_path:
        print("Hoiatus: fpcalc (Chromaprint) ei ole installitud.")
        print("Audio fingerprinting funktsioon ei tööta ilma selleta.")
        print("")
        print("Installimisjuhised:")
        print("  macOS:   brew install chromaprint")
        print("  Ubuntu:  sudo apt install libchromaprint-tools")
        print("  Windows: Laadi alla https://acoustid.org/chromaprint")
        print("")
        return False
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MP3 Tag Editor - MP3 failide metaandmete haldamine"
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='MP3 Tag Editor 1.0'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Kontrolli sõltuvusi ja välju'
    )
    parser.add_argument(
        'file',
        nargs='?',
        help='MP3 fail või kataloog avamiseks'
    )

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    if args.check:
        print("Kõik sõltuvused on installitud!")
        check_chromaprint()
        sys.exit(0)

    # Check chromaprint (non-blocking warning)
    check_chromaprint()

    # Import and run GUI
    from gui.main_window import run_app
    run_app()


if __name__ == '__main__':
    main()
