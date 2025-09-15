"""Tests for async_wrapper service to improve coverage from 51% to 80%+."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nedc_bench.api.services.async_wrapper import AsyncEvaluationWrapper
from nedc_bench.models.annotations import EventAnnotation


@pytest.fixture
def wrapper():
    """Create wrapper instance."""
    return AsyncEvaluationWrapper()


@pytest.mark.asyncio
async def test_evaluate_alpha_success(wrapper):
    """Test successful Alpha pipeline evaluation."""
    with patch.object(wrapper, "_run_alpha_sync") as mock_alpha:
        mock_alpha.return_value = {
            "dp": {"true_positives": 10, "false_positives": 2},
            "epoch": {"true_positives": 8, "false_positives": 3}
        }

        result = await wrapper.evaluate_alpha(
            ref_file="ref.csv",
            hyp_file="hyp.csv",
            algorithms=["dp", "epoch"]
        )

        assert "dp" in result
        assert "epoch" in result
        assert result["dp"]["true_positives"] == 10
        mock_alpha.assert_called_once_with("ref.csv", "hyp.csv", ["dp", "epoch"])


@pytest.mark.asyncio
async def test_evaluate_beta_success(wrapper):
    """Test successful Beta pipeline evaluation."""
    ref_events = [
        EventAnnotation(start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0)
    ]
    hyp_events = [
        EventAnnotation(start_time=0.5, stop_time=1.5, label="seiz", confidence=1.0)
    ]

    with patch.object(wrapper, "_run_beta_sync") as mock_beta:
        mock_beta.return_value = {
            "dp": {"true_positives": 1, "false_positives": 0},
            "epoch": {"true_positives": 1, "false_positives": 0}
        }

        result = await wrapper.evaluate_beta(
            ref_events=ref_events,
            hyp_events=hyp_events,
            algorithms=["dp", "epoch"]
        )

        assert "dp" in result
        assert result["dp"]["true_positives"] == 1
        mock_beta.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_with_parity_success(wrapper):
    """Test evaluation with parity validation enabled."""
    with patch.object(wrapper, "_run_alpha_sync") as mock_alpha, \
         patch.object(wrapper, "_run_beta_sync") as mock_beta, \
         patch.object(wrapper, "_validate_parity") as mock_parity:

        alpha_result = {"dp": {"true_positives": 10}}
        beta_result = {"dp": {"true_positives": 10}}
        parity_result = {"dp": {"parity": True, "discrepancies": []}}

        mock_alpha.return_value = alpha_result
        mock_beta.return_value = beta_result
        mock_parity.return_value = parity_result

        result = await wrapper.evaluate_with_parity(
            ref_file="ref.csv",
            hyp_file="hyp.csv",
            ref_events=[],
            hyp_events=[],
            algorithms=["dp"]
        )

        assert result["alpha"] == alpha_result
        assert result["beta"] == beta_result
        assert result["parity"] == parity_result


@pytest.mark.asyncio
async def test_run_alpha_sync_error_handling(wrapper):
    """Test Alpha sync error handling."""
    with patch("nedc_bench.api.services.async_wrapper.AlphaWrapper") as mock_class:
        mock_instance = MagicMock()
        mock_instance.evaluate.side_effect = Exception("Alpha failed")
        mock_class.return_value = mock_instance

        with pytest.raises(Exception, match="Alpha failed"):
            wrapper._run_alpha_sync("ref.csv", "hyp.csv", ["dp"])


@pytest.mark.asyncio
async def test_run_beta_sync_error_handling(wrapper):
    """Test Beta sync error handling."""
    with patch("nedc_bench.api.services.async_wrapper.BetaPipeline") as mock_class:
        mock_instance = MagicMock()
        mock_instance.evaluate.side_effect = Exception("Beta failed")
        mock_class.return_value = mock_instance

        with pytest.raises(Exception, match="Beta failed"):
            wrapper._run_beta_sync([], [], ["dp"])


@pytest.mark.asyncio
async def test_validate_parity_sync(wrapper):
    """Test parity validation sync execution."""
    with patch("nedc_bench.api.services.async_wrapper.ParityValidator") as mock_class:
        mock_instance = MagicMock()
        mock_instance.validate_batch.return_value = {
            "dp": {"parity": True, "discrepancies": []}
        }
        mock_class.return_value = mock_instance

        alpha_results = {"dp": {"true_positives": 10}}
        beta_results = {"dp": {"true_positives": 10}}

        result = wrapper._validate_parity(alpha_results, beta_results, ["dp"])

        assert result["dp"]["parity"] is True
        mock_instance.validate_batch.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_evaluation(wrapper):
    """Test concurrent evaluation of multiple algorithms."""
    with patch.object(wrapper, "_run_alpha_sync") as mock_alpha:
        # Simulate delay to test concurrency
        async def delayed_alpha(*args):
            await asyncio.sleep(0.1)
            return {"dp": {"result": 1}, "epoch": {"result": 2}}

        mock_alpha.side_effect = lambda *args: asyncio.run(delayed_alpha(*args))

        # Run multiple evaluations concurrently
        tasks = [
            wrapper.evaluate_alpha("ref1.csv", "hyp1.csv", ["dp"]),
            wrapper.evaluate_alpha("ref2.csv", "hyp2.csv", ["epoch"])
        ]

        # Should complete faster than sequential execution
        results = await asyncio.gather(*tasks)
        assert len(results) == 2