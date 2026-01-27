"""Configuration settings for the MP3 Tag Editor application."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class APIConfig:
    """API configuration for various services."""
    lastfm_api_key: str = ""
    discogs_token: str = ""
    acoustid_api_key: str = ""


@dataclass
class AppConfig:
    """Application configuration."""
    # API settings
    api: APIConfig = field(default_factory=APIConfig)

    # Artwork settings
    artwork_size: int = 500  # Target size for album artwork (pixels)
    artwork_quality: int = 90  # JPEG quality (1-100)

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_days: int = 7  # How long to keep cached data

    # UI settings
    show_preview: bool = True  # Show preview before applying changes
    dark_mode: bool = False
    language: str = ""  # Empty = auto-detect from system

    # Fingerprinting
    use_fingerprinting: bool = True

    # Paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".mp3_tag_editor")
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".mp3_tag_editor" / "cache")

    def __post_init__(self):
        """Ensure directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config() -> AppConfig:
    """Load configuration from file or create default."""
    config_file = Path.home() / ".mp3_tag_editor" / "config.json"

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            api_config = APIConfig(
                lastfm_api_key=data.get('api', {}).get('lastfm_api_key', ''),
                discogs_token=data.get('api', {}).get('discogs_token', ''),
                acoustid_api_key=data.get('api', {}).get('acoustid_api_key', '')
            )

            return AppConfig(
                api=api_config,
                artwork_size=data.get('artwork_size', 500),
                artwork_quality=data.get('artwork_quality', 90),
                cache_enabled=data.get('cache_enabled', True),
                cache_ttl_days=data.get('cache_ttl_days', 7),
                show_preview=data.get('show_preview', True),
                dark_mode=data.get('dark_mode', False),
                language=data.get('language', ''),
                use_fingerprinting=data.get('use_fingerprinting', True)
            )
        except (json.JSONDecodeError, KeyError):
            pass

    return AppConfig()


def save_config(config: AppConfig) -> None:
    """Save configuration to file."""
    config_file = config.config_dir / "config.json"

    data = {
        'api': {
            'lastfm_api_key': config.api.lastfm_api_key,
            'discogs_token': config.api.discogs_token,
            'acoustid_api_key': config.api.acoustid_api_key
        },
        'artwork_size': config.artwork_size,
        'artwork_quality': config.artwork_quality,
        'cache_enabled': config.cache_enabled,
        'cache_ttl_days': config.cache_ttl_days,
        'show_preview': config.show_preview,
        'dark_mode': config.dark_mode,
        'language': config.language,
        'use_fingerprinting': config.use_fingerprinting
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# User agent for HTTP requests
USER_AGENT = "MP3TagEditor/1.0 (https://github.com/example/mp3-tag-editor)"

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.mp3'}

# MusicBrainz settings
MUSICBRAINZ_APP_NAME = "MP3TagEditor"
MUSICBRAINZ_APP_VERSION = "1.0"
MUSICBRAINZ_CONTACT = "your@email.com"
