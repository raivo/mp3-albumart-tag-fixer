"""Web image search provider for album artwork."""

from typing import Optional
import httpx
import re
import json
from urllib.parse import quote_plus, urlencode

from .base import ArtworkProvider, ArtworkResult
from config import USER_AGENT


class GoogleImagesProvider(ArtworkProvider):
    """
    Fetches artwork using web image search.

    This is a fallback provider for music not found in other databases,
    especially useful for local/regional music (like Estonian music).
    Uses Bing Image Search (no API key required).
    """

    name = "Web Search"

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            },
            follow_redirects=True
        )

    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """Search for album artwork using web search."""
        results = []

        # Build search query
        query = f"{artist} {album} album cover"

        try:
            results = self._search_bing_images(query)

            # If no results, try alternative queries
            if not results:
                results = self._search_bing_images(f"{artist} {album}")

            if not results:
                results = self._search_bing_images(f"{artist} album cover")

        except Exception as e:
            print(f"Error in web search: {e}")

        return results

    def _search_bing_images(self, query: str) -> list[ArtworkResult]:
        """Search images using Bing."""
        results = []

        try:
            # Bing image search URL
            search_url = "https://www.bing.com/images/search"
            params = {
                'q': query,
                'form': 'HDRSC2',
                'first': '1',
                'tsc': 'ImageBasicHover'
            }

            response = self.client.get(search_url, params=params)

            if response.status_code == 200:
                # Extract image data from HTML
                # Bing embeds image data in 'murl' (media URL) attributes
                html = response.text

                # Find all image entries using regex
                # Looking for murl:"http..." pattern
                murl_pattern = r'murl&quot;:&quot;(https?://[^&]+)&quot;'
                turl_pattern = r'turl&quot;:&quot;(https?://[^&]+)&quot;'

                murls = re.findall(murl_pattern, html)
                turls = re.findall(turl_pattern, html)

                # Also try JSON-style pattern
                if not murls:
                    murl_pattern2 = r'"murl":"(https?://[^"]+)"'
                    turl_pattern2 = r'"turl":"(https?://[^"]+)"'
                    murls = re.findall(murl_pattern2, html)
                    turls = re.findall(turl_pattern2, html)

                for i, murl in enumerate(murls[:12]):  # Limit to 12 results
                    # Clean URL (unescape)
                    image_url = murl.replace('\\u002f', '/').replace('\\/', '/')

                    # Get thumbnail if available
                    thumb_url = turls[i] if i < len(turls) else None
                    if thumb_url:
                        thumb_url = thumb_url.replace('\\u002f', '/').replace('\\/', '/')

                    # Skip if not a valid image URL
                    if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        # Still include, might be dynamic URL
                        pass

                    result = ArtworkResult(
                        image_url=image_url,
                        thumbnail_url=thumb_url,
                        source='Web Search',
                        score=0.6
                    )
                    results.append(result)

        except Exception as e:
            print(f"Bing search error: {e}")

        # If Bing didn't work, try DuckDuckGo lite
        if not results:
            results = self._search_duckduckgo(query)

        return results

    def _search_duckduckgo(self, query: str) -> list[ArtworkResult]:
        """Fallback search using DuckDuckGo."""
        results = []

        try:
            # DuckDuckGo instant answers API (limited but works)
            response = self.client.get(
                "https://api.duckduckgo.com/",
                params={
                    'q': query,
                    'format': 'json',
                    'no_html': '1',
                    'skip_disambig': '1'
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Check for image in response
                image_url = data.get('Image')
                if image_url:
                    if not image_url.startswith('http'):
                        image_url = f"https://duckduckgo.com{image_url}"

                    results.append(ArtworkResult(
                        image_url=image_url,
                        source='Web Search',
                        score=0.7
                    ))

                # Check related topics for images
                for topic in data.get('RelatedTopics', [])[:5]:
                    icon = topic.get('Icon', {})
                    if icon and icon.get('URL'):
                        icon_url = icon['URL']
                        if not icon_url.startswith('http'):
                            icon_url = f"https://duckduckgo.com{icon_url}"

                        results.append(ArtworkResult(
                            image_url=icon_url,
                            source='Web Search',
                            score=0.5
                        ))

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")

        return results

    def search_custom(self, query: str) -> list[ArtworkResult]:
        """Search with a custom query string."""
        return self._search_bing_images(query)

    def get_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            # Use different headers for image download
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': 'https://www.bing.com/'
            }

            response = self.client.get(url, headers=headers, follow_redirects=True, timeout=15.0)

            if response.status_code == 200:
                content = response.content
                content_type = response.headers.get('content-type', '')

                # Accept if content-type indicates image
                if 'image' in content_type:
                    return content

                # Check for common image magic bytes
                if len(content) > 8:
                    if (content[:2] == b'\xff\xd8' or      # JPEG
                        content[:8] == b'\x89PNG\r\n\x1a\n' or  # PNG
                        content[:4] == b'\x89PNG' or       # PNG (short)
                        content[:6] in (b'GIF87a', b'GIF89a') or  # GIF
                        content[:4] == b'RIFF'):           # WebP
                        return content

                # If it's reasonably sized and from image URL, try it anyway
                if len(content) > 1000 and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    return content

        except Exception as e:
            print(f"Error downloading image from {url}: {e}")

        return None

    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'client'):
            self.client.close()
