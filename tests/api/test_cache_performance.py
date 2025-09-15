"""Integration tests for Redis caching performance in the NEDC Bench API."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nedc_bench.api.services.async_wrapper import AsyncOrchestrator
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
class TestCacheIntegration:
    """Test cache integration with AsyncOrchestrator."""

    async def test_cache_hit_skips_evaluation(self, sample_files):
        """Verify cache hit prevents actual evaluation."""
        ref_file, hyp_file = sample_files

        # Mock the orchestrator's evaluate method
        with patch.object(AsyncOrchestrator, "__init__", lambda self, *args: None):
            orchestrator = AsyncOrchestrator()
            orchestrator.executor = MagicMock()
            orchestrator.orchestrator = MagicMock()
            orchestrator.cache = AsyncMock()

            # Simulate cache hit
            cached_result = {
                "alpha_result": {"score": 0.95},
                "beta_result": {"score": 0.95},
                "parity_passed": True,
                "cached": True
            }
            orchestrator.cache.get_json.return_value = cached_result
            orchestrator.cache.make_key.return_value = "test_key"

            # Call evaluate
            result = await orchestrator.evaluate(ref_file, hyp_file, "taes", "dual")

            # Verify cache was checked
            orchestrator.cache.get_json.assert_called_once()

            # Verify actual evaluation was NOT called
            assert not orchestrator.orchestrator.evaluate.called

            # Verify result matches cached data
            assert result == cached_result

    async def test_cache_miss_triggers_evaluation(self, sample_files):
        """Verify cache miss triggers actual evaluation and stores result."""
        ref_file, hyp_file = sample_files

        with patch.object(AsyncOrchestrator, "__init__", lambda self, *args: None):
            orchestrator = AsyncOrchestrator()
            orchestrator.executor = MagicMock()
            orchestrator.cache = AsyncMock()

            # Simulate cache miss
            orchestrator.cache.get_json.return_value = None
            orchestrator.cache.make_key.return_value = "test_key"

            # Mock actual evaluation
            mock_result = MagicMock()
            mock_result.alpha_result = {"score": 0.90}
            mock_result.beta_result = MagicMock()
            mock_result.beta_result.__dict__ = {"score": 0.90}
            mock_result.parity_passed = True
            mock_result.parity_report = MagicMock()
            mock_result.parity_report.to_dict.return_value = {"details": "passed"}
            mock_result.execution_time_alpha = 1.5
            mock_result.execution_time_beta = 0.5
            mock_result.speedup = 3.0

            # Setup the mock to return our result
            loop = asyncio.get_event_loop()
            orchestrator.orchestrator = MagicMock()
            orchestrator.orchestrator.evaluate.return_value = mock_result

            # Patch run_in_executor to call the function directly
            async def mock_run_in_executor(executor, func, *args):
                return func(*args)

            with patch.object(loop, "run_in_executor", mock_run_in_executor):
                result = await orchestrator.evaluate(ref_file, hyp_file, "taes", "dual")

            # Verify cache was checked
            orchestrator.cache.get_json.assert_called_once()

            # Verify result was stored in cache
            orchestrator.cache.set_json.assert_called_once()
            call_args = orchestrator.cache.set_json.call_args
            assert call_args[0][0] == "test_key"  # key
            assert "alpha_result" in call_args[0][1]  # stored data

    async def test_alpha_pipeline_no_caching(self, sample_files):
        """Verify alpha pipeline does not use caching."""
        ref_file, hyp_file = sample_files

        with patch.object(AsyncOrchestrator, "__init__", lambda self, *args: None):
            orchestrator = AsyncOrchestrator()
            orchestrator.executor = MagicMock()
            orchestrator.cache = AsyncMock()
            orchestrator.cache.make_key.return_value = "test_key"

            # Mock alpha evaluation
            alpha_result = {"score": 0.85}
            orchestrator.alpha_wrapper = MagicMock()
            orchestrator.alpha_wrapper.evaluate.return_value = alpha_result

            # Patch run_in_executor
            loop = asyncio.get_event_loop()
            async def mock_run_in_executor(executor, func, *args):
                return func(*args)

            with patch.object(loop, "run_in_executor", mock_run_in_executor):
                result = await orchestrator.evaluate(ref_file, hyp_file, "taes", "alpha")

            # Verify cache was NOT checked or set for alpha pipeline
            orchestrator.cache.get_json.assert_not_called()
            orchestrator.cache.set_json.assert_not_called()

            # Verify result
            assert result == {"alpha_result": alpha_result}


@pytest.mark.asyncio
class TestCachePerformance:
    """Test cache performance improvements."""

    async def test_cache_improves_response_time(self, sample_files):
        """Verify cached responses are significantly faster."""
        ref_file, hyp_file = sample_files

        with patch.object(AsyncOrchestrator, "__init__", lambda self, *args: None):
            orchestrator = AsyncOrchestrator()
            orchestrator.executor = MagicMock()
            orchestrator.cache = AsyncMock()
            orchestrator.cache.make_key.return_value = "perf_test_key"

            # First call - cache miss, slow evaluation
            orchestrator.cache.get_json.return_value = None

            # Mock slow evaluation
            async def slow_evaluation():
                await asyncio.sleep(0.1)  # Simulate processing time
                return {
                    "alpha_result": {"score": 0.95},
                    "beta_result": {"score": 0.95},
                    "parity_passed": True
                }

            # Time first call (cache miss)
            start = time.time()
            orchestrator.cache.get_json.return_value = None

            # Mock the evaluation to take time
            loop = asyncio.get_event_loop()
            mock_result = MagicMock()
            mock_result.alpha_result = {"score": 0.95}
            mock_result.beta_result = MagicMock()
            mock_result.beta_result.__dict__ = {"score": 0.95}
            mock_result.parity_passed = True
            mock_result.parity_report = None
            mock_result.execution_time_alpha = 0.1
            mock_result.execution_time_beta = 0.05
            mock_result.speedup = 2.0

            async def mock_run_in_executor_slow(executor, func, *args):
                await asyncio.sleep(0.1)  # Simulate slow evaluation
                return mock_result

            orchestrator.orchestrator = MagicMock()
            orchestrator.orchestrator.evaluate.return_value = mock_result

            with patch.object(loop, "run_in_executor", mock_run_in_executor_slow):
                result1 = await orchestrator.evaluate(ref_file, hyp_file, "taes", "dual")

            uncached_time = time.time() - start

            # Second call - cache hit, fast response
            cached_data = {
                "alpha_result": {"score": 0.95},
                "beta_result": {"score": 0.95},
                "parity_passed": True
            }
            orchestrator.cache.get_json.return_value = cached_data

            start = time.time()
            result2 = await orchestrator.evaluate(ref_file, hyp_file, "taes", "dual")
            cached_time = time.time() - start

            # Verify cached response is at least 10x faster
            assert cached_time < uncached_time / 10
            assert result2 == cached_data

    async def test_concurrent_cache_requests(self, sample_files):
        """Verify cache handles concurrent requests efficiently."""
        ref_file, hyp_file = sample_files

        with patch.object(AsyncOrchestrator, "__init__", lambda self, *args: None):
            orchestrator = AsyncOrchestrator()
            orchestrator.executor = MagicMock()
            orchestrator.cache = AsyncMock()

            # Setup cache responses
            orchestrator.cache.make_key.return_value = "concurrent_key"
            orchestrator.cache.get_json.return_value = {
                "alpha_result": {"score": 0.95},
                "beta_result": {"score": 0.95},
                "parity_passed": True
            }

            # Launch multiple concurrent requests
            tasks = [
                orchestrator.evaluate(ref_file, hyp_file, "taes", "dual")
                for _ in range(10)
            ]

            start = time.time()
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start

            # All results should be identical
            assert all(r == results[0] for r in results)

            # Should complete quickly (< 100ms for 10 cached requests)
            assert elapsed < 0.1

            # Cache should be hit 10 times
            assert orchestrator.cache.get_json.call_count == 10


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