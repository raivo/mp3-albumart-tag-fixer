"""Unified artwork fetcher that queries all providers."""

from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .providers.base import ArtworkResult
from .providers.musicbrainz import MusicBrainzProvider
from .providers.lastfm import LastFMProvider
from .providers.discogs import DiscogsProvider
from .providers.itunes import ITunesProvider
from .providers.google_images import GoogleImagesProvider
from utils.image_utils import resize_artwork, convert_to_jpeg
from utils.cache import get_cache
from config import get_config


class ArtworkFetcher:
    """Fetches album artwork from multiple sources."""

    def __init__(self):
        self.config = get_config()
        self.cache = get_cache() if self.config.cache_enabled else None

        # Initialize providers
        self.providers = [
            MusicBrainzProvider(),
            ITunesProvider(),
            LastFMProvider(),
            DiscogsProvider(),
            GoogleImagesProvider(),  # Fallback
        ]

    def search(self, artist: str, album: str,
               include_web_search: bool = True) -> list[ArtworkResult]:
        """
        Search for album artwork across all providers.

        Args:
            artist: Artist name
            album: Album name
            include_web_search: Whether to include web search (slower)

        Returns:
            List of ArtworkResult objects sorted by score
        """
        # Check cache first
        cache_key = f"artwork_search:{artist}:{album}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        all_results = []

        # Determine which providers to use
        providers_to_use = []
        for provider in self.providers:
            if provider.name == "Web Search" and not include_web_search:
                continue
            if provider.is_available():
                providers_to_use.append(provider)

        # Search providers in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(provider.search, artist, album): provider
                for provider in providers_to_use
            }

            for future in as_completed(futures, timeout=30):
                provider = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error from {provider.name}: {e}")

        # Sort by score (highest first)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Remove duplicates (same URL)
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.image_url not in seen_urls:
                seen_urls.add(result.image_url)
                unique_results.append(result)

        # Cache results
        if self.cache:
            self.cache.set(cache_key, unique_results)

        return unique_results

    def download(self, result: ArtworkResult,
                 resize: bool = True) -> Optional[bytes]:
        """
        Download artwork from a search result.

        Args:
            result: ArtworkResult to download
            resize: Whether to resize to configured size

        Returns:
            Image bytes (JPEG) or None if failed
        """
        # Check cache
        cache_key = f"artwork_image:{result.image_url}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # Find the provider that provided this result
        provider = self._get_provider_by_name(result.source)
        if not provider:
            # Fallback to any provider that can download
            provider = self.providers[0]

        # Download image
        image_data = provider.get_image(result.image_url)
        if not image_data:
            return None

        # Process image
        try:
            # Convert to JPEG
            image_data = convert_to_jpeg(image_data, self.config.artwork_quality)

            # Resize if requested
            if resize:
                image_data = resize_artwork(image_data, self.config.artwork_size)

            # Cache
            if self.cache:
                self.cache.set(cache_key, image_data)

            return image_data

        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def _get_provider_by_name(self, name: str):
        """Get a provider by its name."""
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None

    def search_custom(self, query: str) -> list[ArtworkResult]:
        """
        Search with a custom query (uses web search).

        Useful for specific searches like "Estonian artist album cover".
        """
        web_provider = self._get_provider_by_name("Web Search")
        if web_provider and hasattr(web_provider, 'search_custom'):
            return web_provider.search_custom(query)
        return []

    def get_thumbnail(self, result: ArtworkResult) -> Optional[bytes]:
        """Get thumbnail image for preview."""
        provider = self._get_provider_by_name(result.source) or self.providers[0]

        # Try thumbnail URL first
        if result.thumbnail_url:
            thumb_data = provider.get_image(result.thumbnail_url)
            if thumb_data:
                return thumb_data

        # Fall back to main image URL
        if result.image_url:
            image_data = provider.get_image(result.image_url)
            if image_data:
                # Create a smaller thumbnail
                try:
                    from utils.image_utils import create_thumbnail
                    return create_thumbnail(image_data, 150)
                except Exception:
                    return image_data

        return None
