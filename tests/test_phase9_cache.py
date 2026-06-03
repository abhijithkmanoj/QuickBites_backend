"""Tests for cache service."""
from app.services import cache
from app.core.config import Settings


def test_cache_key_prefixes_and_defaults():
    assert cache._key("foo") == Settings().CACHE_PREFIX + "foo"


def test_cache_set_disabled_when_flag_off():
    assert cache.set("cache_test_key", {"hello": "world"}, ttl_seconds=60) is False
    assert cache.get("cache_test_key") is None


def test_cache_disabled_by_default():
    assert Settings().USE_REDIS_CACHE is False
