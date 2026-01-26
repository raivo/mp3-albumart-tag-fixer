"""Last.fm artwork provider."""

from typing import Optional
import httpx

from .base import ArtworkProvider, ArtworkResult
from config import get_config, USER_AGENT


class LastFMProvider(ArtworkProvider):
    """Fetches artwork from Last.fm API."""

    name = "Last.fm"

    def __init__(self):
        self.api_url = "https://ws.audioscrobbler.com/2.0/"
        self.config = get_config()
        self.client = httpx.Client(
            timeout=30.0,
            headers={'User-Agent': USER_AGENT}
        )

    def is_available(self) -> bool:
        """Check if Last.fm API key is configured."""
        return bool(self.config.api.lastfm_api_key)

    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """Search for album artwork on Last.fm."""
        if not self.is_available():
            return []

        results = []

        try:
            # Get album info
            response = self.client.get(
                self.api_url,
                params={
                    'method': 'album.getinfo',
                    'api_key': self.config.api.lastfm_api_key,
                    'artist': artist,
                    'album': album,
                    'format': 'json'
                }
            )

            if response.status_code == 200:
                data = response.json()
                album_info = data.get('album', {})

                # Get images of different sizes
                images = album_info.get('image', [])
                for img in images:
                    url = img.get('#text', '')
                    size = img.get('size', '')

                    if url and size == 'extralarge':
                        result = ArtworkResult(
                            image_url=url,
                            source='Last.fm',
                            score=0.9
                        )
                        results.append(result)
                        break  # Only need one size

                # Also get mega size if available
                for img in images:
                    url = img.get('#text', '')
                    size = img.get('size', '')

                    if url and size == 'mega':
                        result = ArtworkResult(
                            image_url=url,
                            source='Last.fm',
                            score=1.0  # Higher score for larger image
                        )
                        results.insert(0, result)  # Add at beginning
                        break

        except httpx.HTTPError as e:
            print(f"Last.fm HTTP error: {e}")
        except Exception as e:
            print(f"Error searching Last.fm: {e}")

        return results

    def search_artist(self, artist: str) -> list[dict]:
        """Search for an artist on Last.fm."""
        if not self.is_available():
            return []

        try:
            response = self.client.get(
                self.api_url,
                params={
                    'method': 'artist.search',
                    'api_key': self.config.api.lastfm_api_key,
                    'artist': artist,
                    'format': 'json',
                    'limit': 5
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('results', {}).get('artistmatches', {}).get('artist', [])

        except Exception as e:
            print(f"Error searching Last.fm artists: {e}")

        return []

    def get_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            response = self.client.get(url, follow_redirects=True)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
        return None

    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'client'):
            self.client.close()
