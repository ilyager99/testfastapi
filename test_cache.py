import pytest
from unittest.mock import patch
from cache import (
    get_cached_url,
    set_cached_url,
    delete_cached_url,
    get_cached_stats,
    set_cached_stats,
    delete_cached_stats,
)
import fakeredis
import time


@pytest.fixture
def mock_redis():
    return fakeredis.FakeRedis(decode_responses=True)


def test_get_set_cached_url(mock_redis):
    with patch("cache.redis_client", mock_redis):
        set_cached_url("abc123", "https://example.com", expire=10)
        assert get_cached_url("abc123") == "https://example.com"

        delete_cached_url("abc123")
        assert get_cached_url("abc123") is None


def test_get_set_cached_stats(mock_redis):
    with patch("cache.redis_client", mock_redis):
        stats = {"clicks": "42", "country": "RU"}
        set_cached_stats("abc123", stats, expire=10)
        assert get_cached_stats("abc123") == stats

        delete_cached_stats("abc123")
        assert get_cached_stats("abc123") == {}


def test_cache_expiration(mock_redis):
    with patch("cache.redis_client", mock_redis):
        set_cached_url("expire_test", "https://example.org", expire=1)
        assert get_cached_url("expire_test") == "https://example.org"

        time.sleep(1.1)
        assert get_cached_url("expire_test") is None

