"""
Distributed cache manager using Upstash Redis for serverless environments.
Falls back to in-memory cache for local development.
"""

import os
import json
import pickle
import pandas as pd
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import upstash-redis, fall back to dict-based cache
try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("upstash-redis not available, using in-memory cache only")


class CacheManager:
    """
    Multi-tier cache manager with Redis (distributed) and in-memory (local) tiers.

    Tier 1: In-memory cache (fastest, per-instance)
    Tier 2: Redis cache (shared across serverless instances)
    Tier 3: Compute on-demand (fallback)
    """

    # Cache version for invalidation
    CACHE_VERSION = "v1"

    # TTL settings (in seconds)
    TTL_CRITICAL = 3600  # 1 hour - summary stats, health distribution
    TTL_ESSENTIAL = 14400  # 4 hours - user table, basic metrics
    TTL_ANALYTICS = 86400  # 24 hours - detailed analytics, cohort data
    TTL_HISTORICAL = 604800  # 7 days - historical data

    def __init__(self):
        """Initialize cache manager with Redis and in-memory cache."""
        self.redis_client = None
        self.memory_cache: Dict[str, tuple] = {}  # {key: (value, expiry)}
        self.cache_hits = 0
        self.cache_misses = 0

        # Initialize Redis if available and configured
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection using Upstash credentials."""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available, using memory-only cache")
            return

        redis_url = os.getenv('UPSTASH_REDIS_REST_URL')
        redis_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')

        if redis_url and redis_token:
            try:
                self.redis_client = Redis(url=redis_url, token=redis_token)
                # Test connection
                self.redis_client.ping()
                logger.info("✓ Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        else:
            logger.info("Redis credentials not found, using memory-only cache")

    def _make_key(self, namespace: str, key: str) -> str:
        """Create versioned cache key."""
        return f"{self.CACHE_VERSION}:{namespace}:{key}"

    def _serialize_dataframe(self, df: pd.DataFrame) -> bytes:
        """Serialize DataFrame efficiently using pickle."""
        return pickle.dumps(df, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize_dataframe(self, data: bytes) -> pd.DataFrame:
        """Deserialize DataFrame from pickle."""
        return pickle.loads(data)

    def _serialize_value(self, value: Any) -> str:
        """Serialize Python objects to JSON string."""
        if isinstance(value, pd.DataFrame):
            raise ValueError("Use set_dataframe for DataFrame objects")
        return json.dumps(value, default=str)

    def _deserialize_value(self, data: str) -> Any:
        """Deserialize JSON string to Python objects."""
        return json.loads(data)

    def get(self, namespace: str, key: str, from_redis: bool = True) -> Optional[Any]:
        """
        Get value from cache (memory first, then Redis).

        Args:
            namespace: Cache namespace (e.g., 'summary', 'users', 'cohorts')
            key: Cache key within namespace
            from_redis: If True, check Redis on memory miss

        Returns:
            Cached value or None if not found
        """
        cache_key = self._make_key(namespace, key)

        # Try memory cache first
        if cache_key in self.memory_cache:
            value, expiry = self.memory_cache[cache_key]
            if datetime.now() < expiry:
                self.cache_hits += 1
                logger.debug(f"Memory cache HIT: {cache_key}")
                return value
            else:
                # Expired, remove from memory
                del self.memory_cache[cache_key]

        # Try Redis if available and requested
        if from_redis and self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data:
                    value = self._deserialize_value(data)
                    # Populate memory cache
                    self._set_memory(cache_key, value, ttl=self.TTL_ESSENTIAL)
                    self.cache_hits += 1
                    logger.debug(f"Redis cache HIT: {cache_key}")
                    return value
            except Exception as e:
                logger.error(f"Redis GET error for {cache_key}: {e}")

        # Cache miss
        self.cache_misses += 1
        logger.debug(f"Cache MISS: {cache_key}")
        return None

    def set(self, namespace: str, key: str, value: Any, ttl: int = None,
            to_redis: bool = True, to_memory: bool = True):
        """
        Set value in cache (both memory and Redis).

        Args:
            namespace: Cache namespace
            key: Cache key within namespace
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: TTL_ESSENTIAL)
            to_redis: If True, save to Redis
            to_memory: If True, save to memory
        """
        if ttl is None:
            ttl = self.TTL_ESSENTIAL

        cache_key = self._make_key(namespace, key)

        # Set in memory cache
        if to_memory:
            self._set_memory(cache_key, value, ttl)

        # Set in Redis
        if to_redis and self.redis_client:
            try:
                serialized = self._serialize_value(value)
                self.redis_client.setex(cache_key, ttl, serialized)
                logger.debug(f"Redis SET: {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"Redis SET error for {cache_key}: {e}")

    def get_dataframe(self, namespace: str, key: str, from_redis: bool = True) -> Optional[pd.DataFrame]:
        """
        Get DataFrame from cache (optimized for DataFrames).

        Args:
            namespace: Cache namespace
            key: Cache key within namespace
            from_redis: If True, check Redis on memory miss

        Returns:
            Cached DataFrame or None if not found
        """
        cache_key = self._make_key(namespace, key)

        # Try memory cache first
        if cache_key in self.memory_cache:
            df, expiry = self.memory_cache[cache_key]
            if datetime.now() < expiry:
                self.cache_hits += 1
                logger.debug(f"Memory cache HIT (DataFrame): {cache_key}")
                return df
            else:
                del self.memory_cache[cache_key]

        # Try Redis if available
        if from_redis and self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data:
                    # Upstash returns string, need to handle encoding
                    if isinstance(data, str):
                        import base64
                        data = base64.b64decode(data)

                    df = self._deserialize_dataframe(data)
                    # Populate memory cache
                    self._set_memory(cache_key, df, ttl=self.TTL_ESSENTIAL)
                    self.cache_hits += 1
                    logger.info(f"Redis cache HIT (DataFrame): {cache_key} - shape {df.shape}")
                    return df
            except Exception as e:
                logger.error(f"Redis GET error for DataFrame {cache_key}: {e}")

        # Cache miss
        self.cache_misses += 1
        logger.debug(f"Cache MISS (DataFrame): {cache_key}")
        return None

    def set_dataframe(self, namespace: str, key: str, df: pd.DataFrame,
                     ttl: int = None, to_redis: bool = True, to_memory: bool = True):
        """
        Set DataFrame in cache (optimized for DataFrames).

        Args:
            namespace: Cache namespace
            key: Cache key within namespace
            df: DataFrame to cache
            ttl: Time-to-live in seconds
            to_redis: If True, save to Redis
            to_memory: If True, save to memory
        """
        if ttl is None:
            ttl = self.TTL_ESSENTIAL

        cache_key = self._make_key(namespace, key)

        # Set in memory cache
        if to_memory:
            self._set_memory(cache_key, df, ttl)

        # Set in Redis (with compression)
        if to_redis and self.redis_client:
            try:
                serialized = self._serialize_dataframe(df)

                # Base64 encode for Upstash REST API
                import base64
                encoded = base64.b64encode(serialized).decode('utf-8')

                self.redis_client.setex(cache_key, ttl, encoded)
                size_mb = len(serialized) / (1024 * 1024)
                logger.info(f"Redis SET (DataFrame): {cache_key} - shape {df.shape}, size {size_mb:.2f}MB, TTL {ttl}s")
            except Exception as e:
                logger.error(f"Redis SET error for DataFrame {cache_key}: {e}")

    def _set_memory(self, cache_key: str, value: Any, ttl: int):
        """Set value in memory cache with expiration."""
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.memory_cache[cache_key] = (value, expiry)
        logger.debug(f"Memory cache SET: {cache_key}")

    def delete(self, namespace: str, key: str):
        """Delete key from both memory and Redis."""
        cache_key = self._make_key(namespace, key)

        # Delete from memory
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

        # Delete from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                logger.info(f"Cache DELETE: {cache_key}")
            except Exception as e:
                logger.error(f"Redis DELETE error for {cache_key}: {e}")

    def invalidate_namespace(self, namespace: str):
        """Invalidate all keys in a namespace."""
        pattern = f"{self.CACHE_VERSION}:{namespace}:*"

        # Clear memory cache
        keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{self.CACHE_VERSION}:{namespace}:")]
        for key in keys_to_delete:
            del self.memory_cache[key]

        # Clear Redis (if available)
        if self.redis_client:
            try:
                # Note: Upstash Redis REST API may not support SCAN
                # For now, we rely on TTL expiration
                logger.info(f"Namespace invalidation requested: {namespace}")
            except Exception as e:
                logger.error(f"Redis namespace invalidation error: {e}")

    def clear_all(self):
        """Clear all caches (use with caution)."""
        self.memory_cache.clear()
        logger.info("Memory cache cleared")

        if self.redis_client:
            try:
                # In production, be careful with FLUSHDB
                # For safety, just log and let TTL expire
                logger.warning("Redis FLUSHDB skipped for safety. Use invalidate_namespace instead.")
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'memory_keys': len(self.memory_cache),
            'redis_connected': self.redis_client is not None
        }


# Global cache manager instance (singleton)
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
