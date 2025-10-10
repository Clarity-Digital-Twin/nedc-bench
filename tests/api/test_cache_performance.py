"""Integration tests for Redis caching performance in the NEDC Bench API."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from nedc_bench.api.services.cache import RedisCache


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    client = AsyncMock()
    client.ping.return_value = True
    client.get.return_value = None  # Cache miss by default
    client.set.return_value = None
    return client


@pytest.fixture
def cache_with_mock_client(mock_redis_client):
    """Create a RedisCache instance with a mocked client."""
    cache = RedisCache()
    cache._client = mock_redis_client
    return cache


@pytest.fixture
def sample_files(tmp_path):
    """Create sample ref/hyp files for testing."""
    ref_file = tmp_path / "ref.csv_bi"
    hyp_file = tmp_path / "hyp.csv_bi"

    ref_content = """version = csv_bi_v1.0.0
patient_id,session,channel,start_time,stop_time,label,confidence
00000001,00000001_01,FP1-F7,0.0000,1.0000,bckg,1.0000
"""
    hyp_content = """version = csv_bi_v1.0.0
patient_id,session,channel,start_time,stop_time,label,confidence
00000001,00000001_01,FP1-F7,0.0000,1.0000,bckg,0.9500
"""

    ref_file.write_text(ref_content)
    hyp_file.write_text(hyp_content)

    return str(ref_file), str(hyp_file)


class TestCacheKeyGeneration:
    """Test cache key generation for consistency and uniqueness."""

    def test_key_generation_consistency(self):
        """Verify that same inputs produce same key."""
        ref_bytes = b"reference content"
        hyp_bytes = b"hypothesis content"

        key1 = RedisCache.make_key(ref_bytes, hyp_bytes, "taes", "dual")
        key2 = RedisCache.make_key(ref_bytes, hyp_bytes, "taes", "dual")

        assert key1 == key2
        assert key1.startswith("nedc:taes:dual:")

    def test_key_uniqueness_different_algorithm(self):
        """Verify different algorithms produce different keys."""
        ref_bytes = b"reference content"
        hyp_bytes = b"hypothesis content"

        key_taes = RedisCache.make_key(ref_bytes, hyp_bytes, "taes", "dual")
        key_dp = RedisCache.make_key(ref_bytes, hyp_bytes, "dp", "dual")

        assert key_taes != key_dp

    def test_key_uniqueness_different_pipeline(self):
        """Verify different pipelines produce different keys."""
        ref_bytes = b"reference content"
        hyp_bytes = b"hypothesis content"

        key_dual = RedisCache.make_key(ref_bytes, hyp_bytes, "taes", "dual")
        key_beta = RedisCache.make_key(ref_bytes, hyp_bytes, "taes", "beta")

        assert key_dual != key_beta

    def test_key_uniqueness_different_content(self):
        """Verify different file contents produce different keys."""
        ref1 = b"reference content 1"
        ref2 = b"reference content 2"
        hyp_bytes = b"hypothesis content"

        key1 = RedisCache.make_key(ref1, hyp_bytes, "taes", "dual")
        key2 = RedisCache.make_key(ref2, hyp_bytes, "taes", "dual")

        assert key1 != key2


@pytest.mark.asyncio
class TestCacheOperations:
    """Test Redis cache operations."""

    async def test_cache_miss_returns_none(self, cache_with_mock_client):
        """Verify cache miss returns None."""
        cache_with_mock_client._client.get.return_value = None

        result = await cache_with_mock_client.get_json("nonexistent_key")
        assert result is None
        cache_with_mock_client._client.get.assert_called_once_with("nonexistent_key")

    async def test_cache_hit_returns_data(self, cache_with_mock_client):
        """Verify cache hit returns stored data."""
        expected_data = {"result": "test_value", "score": 0.95}
        cache_with_mock_client._client.get.return_value = '{"result": "test_value", "score": 0.95}'

        result = await cache_with_mock_client.get_json("test_key")
        assert result == expected_data
        cache_with_mock_client._client.get.assert_called_once_with("test_key")

    async def test_cache_set_stores_data(self, cache_with_mock_client):
        """Verify cache set stores data with TTL."""
        test_data = {"result": "test_value", "score": 0.95}

        await cache_with_mock_client.set_json("test_key", test_data, ttl=3600)

        cache_with_mock_client._client.set.assert_called_once()
        call_args = cache_with_mock_client._client.set.call_args
        assert call_args[0][0] == "test_key"
        assert '"result": "test_value"' in call_args[0][1]
        assert call_args[1]["ex"] == 3600

    async def test_cache_handles_connection_failure(self):
        """Verify cache fails gracefully on connection issues."""
        cache = RedisCache()
        cache._client = None  # Simulate connection failure

        # Should not raise, returns None
        result = await cache.get_json("test_key")
        assert result is None

        # Should not raise
        await cache.set_json("test_key", {"data": "value"})

    async def test_ping_returns_false_on_failure(self, cache_with_mock_client):
        """Verify ping returns False on Redis unavailable."""
        cache_with_mock_client._client.ping.side_effect = Exception("Connection refused")

        result = await cache_with_mock_client.ping()
        assert result is False


@pytest.mark.asyncio
class TestCacheTTL:
    """Test cache TTL behavior."""

    async def test_cache_respects_ttl(self, cache_with_mock_client):
        """Verify cache sets correct TTL on entries."""
        test_data = {"result": "test"}

        # Test default TTL
        await cache_with_mock_client.set_json("key1", test_data)
        call_args = cache_with_mock_client._client.set.call_args
        assert call_args[1]["ex"] == cache_with_mock_client.ttl_seconds

        # Test custom TTL
        await cache_with_mock_client.set_json("key2", test_data, ttl=7200)
        call_args = cache_with_mock_client._client.set.call_args
        assert call_args[1]["ex"] == 7200

    async def test_cache_ttl_from_environment(self, monkeypatch):
        """Verify cache TTL can be configured via environment."""
        monkeypatch.setenv("CACHE_TTL_SECONDS", "3600")

        cache = RedisCache()
        assert cache.ttl_seconds == 3600
