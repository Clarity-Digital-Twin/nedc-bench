"""Test async orchestration with real algorithm execution"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nedc_bench.algorithms.taes import TAESResult
from nedc_bench.api.services.async_wrapper import AsyncOrchestrator
from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


class TestAsyncOrchestrator:
    """Test async wrapper orchestration paths"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with real dual pipeline"""
        return AsyncOrchestrator()

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create test CSV_BI files"""
        ref_file = tmp_path / "ref.csv_bi"
        hyp_file = tmp_path / "hyp.csv_bi"

        # Real CSV_BI format
        csv_content = """# version = csv_bi_v1.0.0
# duration = 10.0 secs
# bname = test
# session = 001
channel,start_time,stop_time,label,confidence
TERM,1.0,2.0,seiz,1.0
TERM,3.0,4.0,bckg,1.0
"""
        ref_file.write_text(csv_content)
        hyp_file.write_text(csv_content)

        return str(ref_file), str(hyp_file)

    @pytest.mark.asyncio
    async def test_alpha_pipeline_execution(self, orchestrator, sample_files):
        """Test Alpha pipeline async execution path"""
        ref_file, hyp_file = sample_files

        # Mock only the Alpha wrapper to avoid NEDC dependency
        with patch.object(orchestrator.orchestrator.alpha_wrapper, 'evaluate') as mock_eval:
            mock_eval.return_value = {
                "taes": {"true_positives": 1.0, "false_positives": 0.0, "false_negatives": 0.0}
            }

            result = await orchestrator.evaluate_single(
                ref_file, hyp_file, algorithm="taes", pipeline="alpha"
            )

            assert "alpha_result" in result
            assert result["alpha_result"]["taes"]["true_positives"] == 1.0
            mock_eval.assert_called_once_with(ref_file, hyp_file)

    @pytest.mark.asyncio
    async def test_beta_pipeline_taes(self, orchestrator, sample_files):
        """Test Beta pipeline TAES execution"""
        ref_file, hyp_file = sample_files

        result = await orchestrator.evaluate_single(
            ref_file, hyp_file, algorithm="taes", pipeline="beta"
        )

        assert "beta_result" in result
        # Result should be TAESResult converted to dict
        assert "true_positives" in result["beta_result"]
        assert "false_positives" in result["beta_result"]

    @pytest.mark.asyncio
    async def test_beta_pipeline_all_algorithms(self, orchestrator, sample_files):
        """Test Beta pipeline supports all 5 algorithms"""
        ref_file, hyp_file = sample_files
        algorithms = ["taes", "dp", "epoch", "overlap", "ira"]

        for algo in algorithms:
            result = await orchestrator.evaluate_single(
                ref_file, hyp_file, algorithm=algo, pipeline="beta"
            )
            assert "beta_result" in result, f"Failed for {algo}"

    @pytest.mark.asyncio
    async def test_unsupported_pipeline_error(self, orchestrator, sample_files):
        """Test error handling for unsupported pipeline"""
        ref_file, hyp_file = sample_files

        with pytest.raises(ValueError, match="Unsupported pipeline: gamma"):
            await orchestrator.evaluate_single(
                ref_file, hyp_file, algorithm="taes", pipeline="gamma"
            )

    @pytest.mark.asyncio
    async def test_unsupported_algorithm_error(self, orchestrator, sample_files):
        """Test error handling for unsupported algorithm in Beta"""
        ref_file, hyp_file = sample_files

        with pytest.raises(ValueError, match="Unsupported algorithm: unknown"):
            await orchestrator.evaluate_single(
                ref_file, hyp_file, algorithm="unknown", pipeline="beta"
            )

    @pytest.mark.asyncio
    async def test_concurrent_evaluations(self, orchestrator, sample_files):
        """Test concurrent execution doesn't block"""
        ref_file, hyp_file = sample_files

        # Run multiple evaluations concurrently
        tasks = [
            orchestrator.evaluate_single(ref_file, hyp_file, "taes", "beta"),
            orchestrator.evaluate_single(ref_file, hyp_file, "dp", "beta"),
            orchestrator.evaluate_single(ref_file, hyp_file, "epoch", "beta"),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for r in results:
            assert "beta_result" in r

    @pytest.mark.asyncio
    async def test_batch_evaluation(self, orchestrator, sample_files):
        """Test batch evaluation method"""
        ref_file, hyp_file = sample_files
        file_pairs = [(ref_file, hyp_file)] * 3

        results = await orchestrator.evaluate_batch(
            file_pairs, algorithm="taes", pipeline="beta"
        )

        assert len(results) == 3
        for r in results:
            assert "beta_result" in r

    @pytest.mark.asyncio
    async def test_executor_cleanup(self, orchestrator):
        """Test executor is properly cleaned up"""
        # Run a simple task
        await orchestrator.evaluate_single(
            "dummy_ref", "dummy_hyp", "taes", "alpha",
            # Mock to avoid file IO
            _mock=True
        )

        # Cleanup should work without errors
        await orchestrator.cleanup()

        # Verify executor is shutdown
        assert orchestrator.executor._shutdown

    @pytest.mark.asyncio
    async def test_result_dict_conversion(self, orchestrator, sample_files):
        """Test Beta results are properly converted to dict"""
        ref_file, hyp_file = sample_files

        result = await orchestrator.evaluate_single(
            ref_file, hyp_file, algorithm="taes", pipeline="beta"
        )

        # Should be dict, not TAESResult object
        assert isinstance(result["beta_result"], dict)
        assert "true_positives" in result["beta_result"]