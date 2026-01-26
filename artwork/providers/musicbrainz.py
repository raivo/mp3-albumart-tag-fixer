"""MusicBrainz/Cover Art Archive provider."""

from typing import Optional
import httpx
import musicbrainzngs

from .base import ArtworkProvider, ArtworkResult
from config import USER_AGENT, MUSICBRAINZ_APP_NAME, MUSICBRAINZ_APP_VERSION, MUSICBRAINZ_CONTACT


# Initialize MusicBrainz
musicbrainzngs.set_useragent(
    MUSICBRAINZ_APP_NAME,
    MUSICBRAINZ_APP_VERSION,
    MUSICBRAINZ_CONTACT
)


class MusicBrainzProvider(ArtworkProvider):
    """Fetches artwork from MusicBrainz Cover Art Archive."""

    name = "MusicBrainz"

    def __init__(self):
        self.caa_url = "https://coverartarchive.org"
        self.client = httpx.Client(
            timeout=30.0,
            headers={'User-Agent': USER_AGENT}
        )

    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """Search for album artwork in Cover Art Archive."""
        results = []

        try:
            # Search for release on MusicBrainz
            search_result = musicbrainzngs.search_releases(
                query=f'release:"{album}" AND artist:"{artist}"',
                limit=5
            )

            release_list = search_result.get('release-list', [])

            for release in release_list:
                release_id = release.get('id')
                if not release_id:
                    continue

                # Check Cover Art Archive for this release
                artwork = self._get_release_artwork(release_id)
                if artwork:
                    # Calculate relevance score based on search score
                    score = float(release.get('ext:score', 0)) / 100.0
                    for art in artwork:
                        art.score = score
                    results.extend(artwork)

        except musicbrainzngs.WebServiceError as e:
            print(f"MusicBrainz search error: {e}")
        except Exception as e:
            print(f"Error searching MusicBrainz: {e}")

        return results

    def _get_release_artwork(self, release_id: str) -> list[ArtworkResult]:
        """Get artwork for a specific release from Cover Art Archive."""
        results = []

        try:
            response = self.client.get(
                f"{self.caa_url}/release/{release_id}",
                follow_redirects=True
            )

            if response.status_code == 200:
                data = response.json()

                for image in data.get('images', []):
                    if image.get('front', False):  # Prefer front cover
                        result = ArtworkResult(
                            image_url=image.get('image', ''),
                            thumbnail_url=image.get('thumbnails', {}).get('500', ''),
                            source='MusicBrainz',
                            score=1.0 if image.get('front') else 0.5
                        )
                        results.append(result)

        except httpx.HTTPError:
            pass  # No artwork available for this release
        except Exception as e:
            print(f"Error fetching CAA artwork: {e}")

        return results

    def search_by_mbid(self, album_mbid: str) -> list[ArtworkResult]:
        """Search for artwork by MusicBrainz release ID."""
        return self._get_release_artwork(album_mbid)

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
