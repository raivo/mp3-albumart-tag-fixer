"""Caching utilities using diskcache."""

from typing import Optional, Any
from pathlib import Path

from diskcache import Cache

from config import get_config


_cache_instance: Optional[Cache] = None


def get_cache() -> Optional[Cache]:
    """
    Get the global cache instance.

    Returns:
        Cache instance or None if caching is disabled
    """
    global _cache_instance

    config = get_config()

    if not config.cache_enabled:
        return None

    if _cache_instance is None:
        cache_dir = config.cache_dir / "http_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        _cache_instance = Cache(
            str(cache_dir),
            size_limit=500 * 1024 * 1024,  # 500 MB limit
            eviction_policy='least-recently-used'
        )

    return _cache_instance


def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None
    """
    cache = get_cache()
    if cache:
        return cache.get(key)
    return None


def cache_set(key: str, value: Any, ttl: int = None) -> None:
    """
    Set a value in cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time-to-live in seconds (uses default if not specified)
    """
    cache = get_cache()
    if cache:
        config = get_config()
        if ttl is None:
            ttl = config.cache_ttl_days * 24 * 60 * 60  # Convert days to seconds
        cache.set(key, value, expire=ttl)


def cache_delete(key: str) -> None:
    """
    Delete a value from cache.

    Args:
        key: Cache key
    """
    cache = get_cache()
    if cache:
        cache.delete(key)


def clear_cache() -> None:
    """Clear all cached data."""
    cache = get_cache()
    if cache:
        cache.clear()


def get_cache_size() -> int:
    """
    Get current cache size in bytes.

    Returns:
        Cache size in bytes
    """
    cache = get_cache()
    if cache:
        return cache.volume()
    return 0


def close_cache() -> None:
    """Close the cache connection."""
    global _cache_instance
    if _cache_instance:
        _cache_instance.close()
        _cache_instance = None
