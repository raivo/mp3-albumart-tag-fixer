"""iTunes/Apple Music artwork provider."""

from typing import Optional
import httpx
import re

from .base import ArtworkProvider, ArtworkResult
from config import USER_AGENT


class ITunesProvider(ArtworkProvider):
    """Fetches artwork from iTunes Search API."""

    name = "iTunes"

    def __init__(self):
        self.api_url = "https://itunes.apple.com/search"
        self.client = httpx.Client(
            timeout=30.0,
            headers={'User-Agent': USER_AGENT}
        )

    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """Search for album artwork on iTunes."""
        results = []

        try:
            # Search for album
            response = self.client.get(
                self.api_url,
                params={
                    'term': f"{artist} {album}",
                    'entity': 'album',
                    'limit': 5
                }
            )

            if response.status_code == 200:
                data = response.json()

                for item in data.get('results', []):
                    artwork_url = item.get('artworkUrl100', '')

                    if artwork_url:
                        # Get high resolution version (replace 100x100 with larger size)
                        hi_res_url = self._get_high_res_url(artwork_url)

                        result = ArtworkResult(
                            image_url=hi_res_url,
                            thumbnail_url=artwork_url,
                            source='iTunes',
                            score=0.9
                        )
                        results.append(result)

        except httpx.HTTPError as e:
            print(f"iTunes HTTP error: {e}")
        except Exception as e:
            print(f"Error searching iTunes: {e}")

        return results

    def _get_high_res_url(self, url: str, size: int = 600) -> str:
        """
        Convert iTunes artwork URL to high resolution.

        iTunes URLs typically end with dimensions like 100x100bb.jpg
        We can request larger sizes up to about 3000x3000.
        """
        # Pattern to match the size portion
        pattern = r'(\d+x\d+)bb'
        replacement = f'{size}x{size}bb'

        return re.sub(pattern, replacement, url)

    def search_by_track(self, artist: str, title: str) -> list[ArtworkResult]:
        """Search for artwork by track instead of album."""
        results = []

        try:
            response = self.client.get(
                self.api_url,
                params={
                    'term': f"{artist} {title}",
                    'entity': 'song',
                    'limit': 5
                }
            )

            if response.status_code == 200:
                data = response.json()

                seen_urls = set()
                for item in data.get('results', []):
                    artwork_url = item.get('artworkUrl100', '')

                    if artwork_url and artwork_url not in seen_urls:
                        seen_urls.add(artwork_url)
                        hi_res_url = self._get_high_res_url(artwork_url)

                        result = ArtworkResult(
                            image_url=hi_res_url,
                            thumbnail_url=artwork_url,
                            source='iTunes',
                            score=0.85  # Slightly lower score for track search
                        )
                        results.append(result)

        except Exception as e:
            print(f"Error searching iTunes tracks: {e}")

        return results

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
