"""Discogs artwork provider."""

from typing import Optional
import httpx

from .base import ArtworkProvider, ArtworkResult
from config import get_config, USER_AGENT


class DiscogsProvider(ArtworkProvider):
    """Fetches artwork from Discogs API."""

    name = "Discogs"

    def __init__(self):
        self.api_url = "https://api.discogs.com"
        self.config = get_config()
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': USER_AGENT,
                'Accept': 'application/json'
            }
        )

    def is_available(self) -> bool:
        """Check if Discogs token is configured."""
        return bool(self.config.api.discogs_token)

    def _get_headers(self) -> dict:
        """Get headers with authorization if available."""
        headers = {}
        if self.config.api.discogs_token:
            headers['Authorization'] = f"Discogs token={self.config.api.discogs_token}"
        return headers

    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """Search for album artwork on Discogs."""
        results = []

        try:
            # Search for release
            response = self.client.get(
                f"{self.api_url}/database/search",
                params={
                    'artist': artist,
                    'release_title': album,
                    'type': 'release',
                    'per_page': 5
                },
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()

                for item in data.get('results', []):
                    # Get cover image
                    cover_url = item.get('cover_image', '')
                    thumb_url = item.get('thumb', '')

                    if cover_url:
                        result = ArtworkResult(
                            image_url=cover_url,
                            thumbnail_url=thumb_url,
                            source='Discogs',
                            score=0.85
                        )
                        results.append(result)

                    # Also try to get master release for better quality
                    master_id = item.get('master_id')
                    if master_id:
                        master_artwork = self._get_master_artwork(master_id)
                        results.extend(master_artwork)

        except httpx.HTTPError as e:
            print(f"Discogs HTTP error: {e}")
        except Exception as e:
            print(f"Error searching Discogs: {e}")

        return results

    def _get_master_artwork(self, master_id: int) -> list[ArtworkResult]:
        """Get artwork from master release."""
        results = []

        try:
            response = self.client.get(
                f"{self.api_url}/masters/{master_id}",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()

                # Get images
                for img in data.get('images', []):
                    if img.get('type') == 'primary':
                        result = ArtworkResult(
                            image_url=img.get('uri', ''),
                            thumbnail_url=img.get('uri150', ''),
                            source='Discogs',
                            width=img.get('width'),
                            height=img.get('height'),
                            score=0.95  # Master releases have high quality images
                        )
                        results.append(result)

        except Exception as e:
            print(f"Error fetching Discogs master: {e}")

        return results

    def get_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            response = self.client.get(
                url,
                follow_redirects=True,
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
        return None

    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'client'):
            self.client.close()
