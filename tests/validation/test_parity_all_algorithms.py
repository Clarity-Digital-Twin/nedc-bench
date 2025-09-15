"""Test parity validator compare_all_algorithms method"""

import pytest
from nedc_bench.algorithms.dp_alignment import DPAlignmentResult
from nedc_bench.algorithms.epoch import EpochResult
from nedc_bench.algorithms.ira import IRAResult
from nedc_bench.algorithms.overlap import OverlapResult
from nedc_bench.algorithms.taes import TAESResult
from nedc_bench.validation.parity import ParityValidator


class TestCompareAllAlgorithms:
    """Test compare_all_algorithms orchestration"""

    @pytest.fixture
    def validator(self):
        """Create validator with default tolerance"""
        return ParityValidator(tolerance=1e-10)

    @pytest.fixture
    def alpha_results(self):
        """Create comprehensive Alpha results dict"""
        return {
            "taes": {
                "true_positives": 10.0,
                "false_positives": 2.0,
                "false_negatives": 1.0,
                "sensitivity": 0.909,
                "precision": 0.833,
                "f1_score": 0.869,
            },
            "dp": {
                "true_positives": 100,
                "false_positives": 5,
                "false_negatives": 3,
                "insertions": 2,
                "deletions": 1,
                "substitutions": 3,
            },
            "epoch": {
                "confusion": {
                    "seiz": {"seiz": 50, "bckg": 5},
                    "bckg": {"seiz": 3, "bckg": 100},
                }
            },
            "overlap": {
                "hits": 45,
                "misses": 5,
                "false_alarms": 3,
            },
            "ira": {
                "multi_class_kappa": 0.85,
                "per_label_kappa": {
                    "seiz": 0.82,
                    "bckg": 0.88,
                },
            },
        }

    @pytest.fixture
    def beta_results(self):
        """Create matching Beta results objects with correct dataclass fields"""
        return {
            "taes": TAESResult(
                true_positives=10.0,
                false_positives=2.0,
                false_negatives=1.0,
            ),
            "dp": DPAlignmentResult(
                hits=100,
                substitutions={},
                insertions={"seiz": 2},
                deletions={"seiz": 1},
                total_insertions=2,
                total_deletions=1,
                total_substitutions=3,
                true_positives=100,
                false_positives=5,
                false_negatives=3,
                aligned_ref=[],
                aligned_hyp=[],
            ),
            "epoch": EpochResult(
                confusion_matrix={
                    "seiz": {"seiz": 50, "bckg": 5},
                    "bckg": {"seiz": 3, "bckg": 100},
                },
                hits={"seiz": 50, "bckg": 100},
                misses={"seiz": 5, "bckg": 3},
                false_alarms={"seiz": 3, "bckg": 5},
                insertions={},
                deletions={},
                compressed_ref=["null", "seiz", "bckg", "null"],
                compressed_hyp=["null", "seiz", "bckg", "null"],
            ),
            "overlap": OverlapResult(
                hits={"seiz": 45},
                misses={"seiz": 5},
                false_alarms={"seiz": 3},
                insertions={"seiz": 3},
                deletions={"seiz": 5},
                total_hits=45,
                total_misses=5,
                total_false_alarms=3,
            ),
            "ira": IRAResult(
                confusion_matrix={
                    "seiz": {"seiz": 50, "bckg": 5},
                    "bckg": {"seiz": 3, "bckg": 100},
                },
                per_label_kappa={"seiz": 0.82, "bckg": 0.88},
                multi_class_kappa=0.85,
                labels=["bckg", "seiz"],
            ),
        }

    def test_compare_all_algorithms_success(self, validator, alpha_results, beta_results):
        """Test successful comparison of all algorithms"""
        reports = validator.compare_all_algorithms(alpha_results, beta_results)

        # Should have report for each algorithm
        assert len(reports) == 5
        assert "taes" in reports
        assert "dp" in reports
        assert "epoch" in reports
        assert "overlap" in reports
        assert "ira" in reports

        # All should pass with matching data
        for algo, report in reports.items():
            assert report.passed, f"{algo} should pass parity"
            assert report.algorithm.upper() == algo.upper() or report.algorithm == "DP_ALIGNMENT"

    def test_compare_partial_algorithms(self, validator, alpha_results, beta_results):
        """Test comparison with only subset of algorithms"""
        # Remove some algorithms from Alpha
        partial_alpha = {
            "taes": alpha_results["taes"],
            "epoch": alpha_results["epoch"],
        }

        reports = validator.compare_all_algorithms(partial_alpha, beta_results)

        # Should only have reports for algorithms in both
        assert len(reports) == 2
        assert "taes" in reports
        assert "epoch" in reports
        assert "dp" not in reports
        assert "overlap" not in reports
        assert "ira" not in reports

    def test_compare_missing_beta_algorithms(self, validator, alpha_results):
        """Test comparison when Beta is missing algorithms"""
        partial_beta = {
            "taes": TAESResult(
                true_positives=10.0,
                false_positives=2.0,
                false_negatives=1.0,
            )
        }

        reports = validator.compare_all_algorithms(alpha_results, partial_beta)

        # Should only compare TAES
        assert len(reports) == 1
        assert "taes" in reports

    def test_compare_empty_results(self, validator):
        """Test comparison with empty result dicts"""
        reports = validator.compare_all_algorithms({}, {})

        # Should return empty reports dict
        assert reports == {}

    def test_compare_with_failures(self, validator, alpha_results, beta_results):
        """Test comparison with parity failures"""
        # Modify Beta to cause failures
        beta_results["taes"] = TAESResult(
            true_positives=15.0,  # Wrong value
            false_positives=2.0,
            false_negatives=1.0,
        )

        reports = validator.compare_all_algorithms(alpha_results, beta_results)

        # TAES should fail, others pass
        assert not reports["taes"].passed
        assert reports["dp"].passed
        assert reports["epoch"].passed
        assert reports["overlap"].passed
        assert reports["ira"].passed

        # Check discrepancy details
        assert len(reports["taes"].discrepancies) > 0
        disc = reports["taes"].discrepancies[0]
        assert disc.metric == "true_positives"
        assert disc.alpha_value == 10.0
        assert disc.beta_value == 15.0

    def test_compare_mixed_presence(self, validator):
        """Test with algorithms present in different combinations"""
        alpha = {
            "taes": {"true_positives": 5.0, "false_positives": 0.0, "false_negatives": 0.0},
            "dp": {"true_positives": 10, "false_positives": 0, "false_negatives": 0},
            # epoch missing
            "overlap": {"hits": 20, "misses": 0, "false_alarms": 0},
            # ira missing
        }

        beta = {
            "taes": TAESResult(true_positives=5.0, false_positives=0.0, false_negatives=0.0),
            # dp missing
            "epoch": EpochResult(
                confusion_matrix={"a": {"a": 1}},
                hits={"a": 1},
                misses={"a": 0},
                false_alarms={"a": 0},
                insertions={},
                deletions={},
                compressed_ref=["a"],
                compressed_hyp=["a"],
            ),
            "overlap": OverlapResult(
                hits={"x": 20},
                misses={"x": 0},
                false_alarms={"x": 0},
                insertions={"x": 0},
                deletions={"x": 0},
                total_hits=20,
                total_misses=0,
                total_false_alarms=0,
            ),
            "ira": IRAResult(confusion_matrix={}, per_label_kappa={}, multi_class_kappa=0.9, labels=[]),
        }

        reports = validator.compare_all_algorithms(alpha, beta)

        # Should only compare algorithms present in both
        assert len(reports) == 2
        assert "taes" in reports
        assert "overlap" in reports
        assert "dp" not in reports  # Missing in beta
        assert "epoch" not in reports  # Missing in alpha
        assert "ira" not in reports  # Missing in alpha

    def test_algorithm_name_mapping(self, validator):
        """Test DP_ALIGNMENT name mapping in reports"""
        alpha = {"dp": {"true_positives": 5, "false_positives": 0, "false_negatives": 0}}
        beta = {"dp": DPAlignmentResult(
            hits=5,
            substitutions={},
            insertions={},
            deletions={},
            total_insertions=0,
            total_deletions=0,
            total_substitutions=0,
            true_positives=5,
            false_positives=0,
            false_negatives=0,
            aligned_ref=[],
            aligned_hyp=[],
        )}

        reports = validator.compare_all_algorithms(alpha, beta)

        assert reports["dp"].algorithm == "DP_ALIGNMENT"  # Should use proper name
