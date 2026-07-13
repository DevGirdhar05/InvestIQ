import json
import redis
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Any

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Default TTLs in seconds
TTL_ANALYSIS   = 900    # 15 minutes — price data
TTL_EXPLANATION= 3600   # 1 hour — explanations rarely change
TTL_SENTIMENT  = 1800   # 30 minutes — news updates slowly
TTL_QA         = 86400  # 24 hours — knowledge base is static


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client. Returns None if Redis is unavailable.
    The API degrades gracefully — works without Redis,
    just slower (no caching).
    """
    try:
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        client = redis.Redis(
            host           = host,
            port           = port,
            db             = 0,
            decode_responses= True,
            socket_timeout = 2   # fail fast if Redis is down
        )
        client.ping()   # raises exception if not connected
        return client
    except Exception:
        return None   # Redis unavailable — continue without cache


# Global client — created once, reused
_redis_client = None

def get_client() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from cache.
    Returns None if key doesn't exist or Redis is unavailable.
    """
    client = get_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = TTL_ANALYSIS):
    """
    Store a value in cache with TTL.
    Silently fails if Redis is unavailable.
    """
    client = get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass   # cache failure should never break the API


def cache_delete(key: str):
    """Manually invalidate a cache entry."""
    client = get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception:
        pass


def cache_flush_pattern(pattern: str):
    """
    Delete all keys matching a pattern.
    e.g. cache_flush_pattern("analyze:*") clears all analysis cache.
    """
    client = get_client()
    if client is None:
        return
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
            print(f"  Cleared {len(keys)} cache entries for '{pattern}'")
    except Exception:
        pass


def get_cache_stats() -> dict:
    """Return cache statistics for the /health endpoint."""
    client = get_client()
    if client is None:
        return {"status": "unavailable"}
    try:
        info = client.info()
        return {
            "status"      : "ok",
            "used_memory" : info["used_memory_human"],
            "total_keys"  : client.dbsize(),
            "hits"        : info.get("keyspace_hits", 0),
            "misses"      : info.get("keyspace_misses", 0),
        }
    except Exception as e:
        return {"status": f"error: {e}"}