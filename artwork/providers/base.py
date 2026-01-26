"""Base class for artwork providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ArtworkResult:
    """Result from an artwork search."""
    image_url: str
    thumbnail_url: Optional[str] = None
    source: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    score: float = 1.0  # Relevance score 0-1


class ArtworkProvider(ABC):
    """Base class for artwork providers."""

    name: str = "base"

    @abstractmethod
    def search(self, artist: str, album: str) -> list[ArtworkResult]:
        """
        Search for album artwork.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            List of ArtworkResult objects
        """
        pass

    @abstractmethod
    def get_image(self, url: str) -> Optional[bytes]:
        """
        Download image from URL.

        Args:
            url: Image URL

        Returns:
            Image bytes or None if failed
        """
        pass

    def is_available(self) -> bool:
        """Check if this provider is properly configured."""
        return True
