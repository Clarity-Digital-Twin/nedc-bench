"""Tests for dual pipeline orchestration"""

import pytest

from nedc_bench.orchestration.dual_pipeline import (
    BetaPipeline,
    DualPipelineOrchestrator,
    DualPipelineResult,
)
from nedc_bench.validation.parity import ValidationReport


@pytest.mark.integration
def test_dual_pipeline_execution(setup_nedc_env, test_data_dir):
    """Run both pipelines and validate results"""
    orchestrator = DualPipelineOrchestrator()

    ref_file = test_data_dir / "ref" / "aaaaaasf_s001_t000.csv_bi"
    hyp_file = test_data_dir / "hyp" / "aaaaaasf_s001_t000.csv_bi"

    result = orchestrator.evaluate(ref_file=str(ref_file), hyp_file=str(hyp_file), algorithm="taes")

    assert result.alpha_result is not None
    assert result.beta_result is not None
    assert result.parity_report is not None
    assert isinstance(result.parity_passed, bool)
    assert result.execution_time_alpha > 0
    assert result.execution_time_beta > 0
    assert result.speedup > 0


def test_beta_pipeline_taes(test_data_dir):
    """Test Beta pipeline TAES evaluation"""
    beta_pipeline = BetaPipeline()

    ref_file = test_data_dir / "ref" / "aaaaaasf_s001_t000.csv_bi"
    hyp_file = test_data_dir / "hyp" / "aaaaaasf_s001_t000.csv_bi"

    result = beta_pipeline.evaluate_taes(ref_file, hyp_file)

    assert hasattr(result, "true_positives")
    assert hasattr(result, "false_positives")
    assert hasattr(result, "false_negatives")
    assert hasattr(result, "sensitivity")
    assert hasattr(result, "precision")
    assert hasattr(result, "f1_score")


def test_dual_pipeline_result():
    """Test DualPipelineResult dataclass"""
    result = DualPipelineResult(
        alpha_result={"taes": {"sensitivity": 0.9}},
        beta_result={"sensitivity": 0.9},
        parity_report=ValidationReport(
            algorithm="TAES", passed=True, discrepancies=[], alpha_metrics={}, beta_metrics={}
        ),
        parity_passed=True,
        execution_time_alpha=1.0,
        execution_time_beta=0.5,
    )

    assert result.speedup == 2.0  # 1.0 / 0.5


def test_dual_pipeline_with_list_files(setup_nedc_env, test_data_dir):
    """Test with list files like Alpha pipeline"""
    ref_list = test_data_dir / "lists" / "ref.list"
    hyp_list = test_data_dir / "lists" / "hyp.list"

    # Skip if list files don't exist
    if not ref_list.exists() or not hyp_list.exists():
        pytest.skip("List files not found")

    orchestrator = DualPipelineOrchestrator()
    result = orchestrator.evaluate_lists(
        ref_list=str(ref_list), hyp_list=str(hyp_list), algorithm="taes"
    )

    assert "file_results" in result
    assert "total_files" in result
    assert isinstance(result["parity_passed"], bool)


def test_unsupported_algorithm(test_data_dir):
    """Test error handling for unsupported algorithm"""
    orchestrator = DualPipelineOrchestrator()

    ref_file = test_data_dir / "ref" / "aaaaaasf_s001_t000.csv_bi"
    hyp_file = test_data_dir / "hyp" / "aaaaaasf_s001_t000.csv_bi"

    with pytest.raises(ValueError, match="not yet implemented"):
        orchestrator.evaluate(
            ref_file=str(ref_file), hyp_file=str(hyp_file), algorithm="unsupported"
        )
