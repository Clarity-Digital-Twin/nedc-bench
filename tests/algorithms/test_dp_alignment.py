"""Test suite for DP Alignment algorithm - TDD approach"""

import pytest

from nedc_bench.algorithms.dp_alignment import NULL_CLASS, DPAligner


class TestDPAlignment:
    """Test DP Alignment following NEDC exact semantics"""

    @pytest.fixture
    def simple_sequences(self) -> tuple[list[str], list[str]]:
        """Simple test case for alignment"""
        ref = ["seiz", "bckg", "seiz", "bckg"]
        hyp = ["bckg", "seiz", "seiz", "bckg"]
        return ref, hyp

    @pytest.fixture
    def null_class_case(self) -> tuple[list[str], list[str]]:
        """Test case requiring NULL_CLASS handling"""
        ref = ["seiz", "seiz", "bckg"]
        hyp = ["bckg", "seiz"]  # Shorter sequence
        return ref, hyp

    @pytest.fixture
    def exact_match_case(self) -> tuple[list[str], list[str]]:
        """Perfect alignment case"""
        ref = ["seiz", "bckg", "seiz"]
        hyp = ["seiz", "bckg", "seiz"]
        return ref, hyp

    def test_dp_aligner_initialization(self):
        """Test aligner initialization with penalties"""
        aligner = DPAligner(penalty_del=1.0, penalty_ins=1.0, penalty_sub=1.0)
        assert aligner.penalty_del == 1.0
        assert aligner.penalty_ins == 1.0
        assert aligner.penalty_sub == 1.0

    def test_exact_match_produces_zero_errors(self, exact_match_case):
        """Test that exact matches produce no errors"""
        ref, hyp = exact_match_case
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # NEDC semantics: exact match = all hits, no errors
        assert result.hits == 3  # All 3 labels match
        assert result.total_insertions == 0
        assert result.total_deletions == 0
        assert result.total_substitutions == 0
        # In NEDC convention, true_positives only counts positive class ("seiz")
        # There are 2 "seiz" matches in ['seiz', 'bckg', 'seiz']
        assert result.true_positives == 2  # Only seiz hits count as TP
        assert result.false_positives == 0
        assert result.false_negatives == 0

    def test_substitution_counting(self, simple_sequences):
        """Test substitution matrix construction"""
        ref, hyp = simple_sequences
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # Expected: ref[0]=seiz vs hyp[0]=bckg is substitution
        assert result.total_substitutions > 0
        assert "seiz" in result.substitutions
        assert "bckg" in result.substitutions["seiz"]
        assert result.substitutions["seiz"]["bckg"] == 1  # INTEGER count

    def test_insertion_deletion_with_null_class(self, null_class_case):
        """Test NULL_CLASS handling for insertions/deletions"""
        ref, hyp = null_class_case
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # Ref is longer, so we expect deletions
        assert result.total_deletions > 0
        # All counts must be integers
        assert isinstance(result.total_deletions, int)
        assert isinstance(result.total_insertions, int)
        assert isinstance(result.hits, int)

    def test_aligned_sequences_include_null_sentinels(self, simple_sequences):
        """Test that aligned sequences include NULL_CLASS sentinels"""
        ref, hyp = simple_sequences
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # NEDC adds NULL_CLASS sentinels at start/end
        assert result.aligned_ref[0] == NULL_CLASS
        assert result.aligned_ref[-1] == NULL_CLASS
        assert result.aligned_hyp[0] == NULL_CLASS
        assert result.aligned_hyp[-1] == NULL_CLASS

    def test_per_label_tracking(self):
        """Test per-label insertion/deletion tracking"""
        ref = ["seiz", "seiz", "bckg"]
        hyp = ["seiz", "null", "bckg", "artf"]  # null causes deletion, artf is insertion

        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # Check per-label dictionaries exist
        assert isinstance(result.insertions, dict)
        assert isinstance(result.deletions, dict)
        # Verify we track individual labels
        if "artf" in result.insertions:
            assert result.insertions["artf"] >= 1

    def test_integer_count_types(self, simple_sequences):
        """Verify all counts are integers per NEDC"""
        ref, hyp = simple_sequences
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # ALL counts must be integers for DP
        assert isinstance(result.hits, int)
        assert isinstance(result.total_insertions, int)
        assert isinstance(result.total_deletions, int)
        assert isinstance(result.total_substitutions, int)
        assert isinstance(result.true_positives, int)
        assert isinstance(result.false_positives, int)
        assert isinstance(result.false_negatives, int)

        # Per-label counts also integers
        for label_dict in [result.insertions, result.deletions]:
            for label, count in label_dict.items():
                assert isinstance(count, int), f"Count for {label} must be int"

        # Substitution matrix entries are integers
        for ref_label in result.substitutions:
            for hyp_label, count in result.substitutions[ref_label].items():
                assert isinstance(count, int), f"Sub count {ref_label}->{hyp_label} must be int"

    def test_aggregate_count_consistency(self):
        """Test that aggregate counts match detailed counts"""
        ref = ["seiz", "bckg", "seiz", "bckg", "artf"]
        hyp = ["seiz", "seiz", "bckg", "bckg", "null"]

        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # Total insertions should match sum of per-label insertions
        if result.insertions:
            assert result.total_insertions == sum(result.insertions.values())

        # Total deletions should match sum of per-label deletions
        if result.deletions:
            assert result.total_deletions == sum(result.deletions.values())

        # Total substitutions should match sum of substitution matrix
        total_subs = sum(
            count
            for ref_label in result.substitutions
            for count in result.substitutions[ref_label].values()
        )
        assert result.total_substitutions == total_subs

        # In NEDC EEG convention, FN only counts misses for positive class ("seiz")
        # FN = deletions of seiz + substitutions from seiz
        seiz_deletions = result.deletions.get("seiz", 0)
        seiz_substitutions = sum(result.substitutions.get("seiz", {}).values())
        assert result.false_negatives == seiz_deletions + seiz_substitutions
