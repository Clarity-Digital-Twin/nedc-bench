# Phase 3: Core Algorithms — Final Plan (Corrected)
## Vertical Slice Goal: All 5 Algorithms with Full Parity Validation (DP, Epoch, Overlap, TAES, IRA)

### Duration: 10 Days (2 Weeks)

### Success Criteria (TDD)
- [ ] All 4 remaining algorithms implemented under `nedc_bench/algorithms/`
- [ ] 100% unit test coverage on each algorithm’s core logic
- [ ] Counts-first parity with Alpha (metrics recomputed centrally)
- [ ] Comprehensive validation suite passes (`atol=1e-10` for floats)
- [ ] Performance metrics documented

### Ground Rules
- Code lives under `nedc_bench/`; tests under `tests/`.
- Use `alpha/wrapper.NEDCAlphaWrapper` with `NEDC_NFC` for Alpha runs.
- Apply NEDC label map (lowercased) for all algorithms before scoring.
- Compare counts first; recompute floats centrally to avoid print rounding drift.
- Rounding/tolerance: DP/Epoch/Overlap counts (ints) exact; IRA floats (`kappa`, per-label) with `atol=1e-10`.

### Days 1-2: Dynamic Programming Alignment

#### Day 1 Morning: DP Algorithm Core (Counts + Path for debug)
```python
# tests/test_dp_alignment.py
from nedc_bench.algorithms.dp_alignment import DPAligner

def test_dp_exact_alignment_counts():
    ref = ["seiz", "bckg", "seiz"]
    hyp = ["seiz", "bckg", "seiz"]

    result = DPAligner().align(ref, hyp)

    # Counts-first checks (NEDC DP reports counts + metrics)
    assert result.true_positives == 3
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.sensitivity == 1.0
```

#### Day 1 Afternoon: DP Edge Cases
```python
# nedc_bench/algorithms/dp_alignment.py
import numpy as np
from typing import List, Tuple

class DPAligner:
    """Dynamic Programming alignment for event sequences"""

    def __init__(self,
                 penalty_del: float = 1.0,
                 penalty_ins: float = 1.0,
                 penalty_sub: float = 1.0):
        self.penalties = {
            'deletion': penalty_del,
            'insertion': penalty_ins,
            'substitution': penalty_sub
        }

    def align(self, ref: List[str], hyp: List[str]) -> AlignmentResult:
        """Classic DP alignment with NEDC-compatible counts"""
        m, n = len(ref), len(hyp)
        dp = np.zeros((m + 1, n + 1))

        # Initialize base cases
        for i in range(1, m + 1):
            dp[i][0] = i * self.penalties['deletion']
        for j in range(1, n + 1):
            dp[0][j] = j * self.penalties['insertion']

        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref[i-1] == hyp[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + self.penalties['deletion'],
                        dp[i][j-1] + self.penalties['insertion'],
                        dp[i-1][j-1] + self.penalties['substitution']
                    )

        return self._traceback(dp, ref, hyp)  # Produces counts + optional path
```

#### Day 2: DP Parity Testing
```python
# tests/test_dp_parity.py
from nedc_bench.validation.parity import ParityValidator
from nedc_bench.algorithms.dp_alignment import DPAligner

def test_dp_parity_simple():
    ref = ["seiz", "bckg", "seiz"]
    hyp = ["seiz", "bckg", "bckg"]

    # Alpha (stubbed values for illustration; in real tests, use wrapper)
    alpha = {"true_positives": 2, "false_positives": 0, "false_negatives": 1}

    # Beta
    beta_counts = DPAligner().align(ref, hyp).counts_dict()
    report = ParityValidator().compare_dp(alpha, beta_counts)
    assert report.passed
```

### Days 3-4: Epoch-Based Scoring

#### Day 3 Morning: Epoch Segmentation
```python
# tests/test_epoch_scoring.py
def test_epoch_window_segmentation():
    """Test fixed-window segmentation"""
    duration = 10.0
    epoch_size = 0.25

    epochs = EpochScorer.create_epochs(duration, epoch_size)

    assert len(epochs) == 40
    assert epochs[0] == (0.0, 0.25)
    assert epochs[-1] == (9.75, 10.0)
```

#### Day 3 Afternoon: Epoch Classification
```python
# nedc_bench/algorithms/epoch.py
from typing import List, Tuple
import numpy as np

class EpochScorer:
    """Fixed-window epoch-based scoring"""

    def __init__(self, epoch_duration: float = 0.25):
        self.epoch_duration = epoch_duration

    def score(self,
              reference: List[EventAnnotation],
              hypothesis: List[EventAnnotation],
              file_duration: float) -> EpochResult:
        """Score using fixed-time epochs"""

        # Create epoch windows
        epochs = self.create_epochs(file_duration, self.epoch_duration)

        # Classify each epoch
        ref_labels = self.classify_epochs(epochs, reference)
        hyp_labels = self.classify_epochs(epochs, hypothesis)

        # Compute metrics
        return self.compute_metrics(ref_labels, hyp_labels)

    def classify_epochs(self,
                        epochs: List[Tuple[float, float]],
                        events: List[EventAnnotation]) -> List[str]:
        """Classify each epoch based on events"""
        labels = []

        for start, end in epochs:
            # Find dominant label in this epoch
            label = self.get_epoch_label(start, end, events)
            labels.append(label)

        return labels
```

#### Day 4: Epoch Validation
```python
# tests/test_epoch_parity.py
def test_epoch_cohen_kappa():
    """Verify Cohen's kappa calculation"""
    ref_labels = ["seiz", "bckg", "seiz", "bckg"]
    hyp_labels = ["seiz", "bckg", "bckg", "bckg"]

    scorer = EpochScorer()
    result = scorer.compute_kappa(ref_labels, hyp_labels)

    # Verify against sklearn for correctness
    from sklearn.metrics import cohen_kappa_score
    expected = cohen_kappa_score(ref_labels, hyp_labels)

    assert abs(result - expected) < 1e-10
```

### Days 5-6: Overlap Scoring (NEDC semantics)

#### Day 5 Morning: Temporal Overlap
```python
# tests/test_overlap_scoring.py
from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.models.annotations import EventAnnotation

def test_overlap_guard_and_threshold():
    ref = EventAnnotation(start_time=10.0, stop_time=20.0, label="seiz", confidence=1.0)
    hyp = EventAnnotation(start_time=9.999, stop_time=20.001, label="seiz", confidence=1.0)

    scorer = OverlapScorer(guard_width=0.001)
    result = scorer.score([ref], [hyp])

    # With guard width, should be a perfect match at threshold 0.0
    assert result.true_positives == 1
    assert result.false_positives == 0
    assert result.false_negatives == 0
```

#### Day 5 Afternoon: Overlap Metrics
```python
# nedc_bench/algorithms/overlap.py
class OverlapScorer:
    """Temporal overlap-based scoring"""

    def score(self,
              reference: List[EventAnnotation],
              hypothesis: List[EventAnnotation]) -> OverlapResult:
        """Score based on temporal overlap"""

        # Build overlap matrix
        overlap_matrix = self.build_overlap_matrix(reference, hypothesis)

        # Compute final counts (ints) per NEDC semantics
        tp, fp, fn, tn = self.count_events(overlap_matrix)
        return OverlapResult(true_positives=tp, false_positives=fp, false_negatives=fn, true_negatives=tn)
```

#### Day 6: Overlap Validation
```python
# tests/test_overlap_parity.py
def test_overlap_guard_width():
    """Test guard width boundary handling"""
    ref = EventAnnotation(start_time=10.0, stop_time=20.0)
    hyp = EventAnnotation(start_time=9.999, stop_time=20.001)

    scorer = OverlapScorer(guard_width=0.001)
    result = scorer.score([ref], [hyp])

    # Should be considered perfect match with guard width
    assert result.metrics[0]['sensitivity'] == 1.0
```

### Days 7-8: Inter-Rater Agreement

#### Day 7 Morning: IRA Statistics
```python
# tests/test_ira_scoring.py
def test_ira_perfect_agreement():
    """Test perfect inter-rater agreement"""
    rater1 = ["seiz", "bckg", "seiz"]
    rater2 = ["seiz", "bckg", "seiz"]

    scorer = IRAScorer()
    result = scorer.compute_agreement(rater1, rater2)

    assert result.percent_agreement == 1.0
    assert result.cohen_kappa == 1.0
```

#### Day 7 Afternoon: Multi-class IRA
```python
# nedc_bench/algorithms/ira.py
from sklearn.metrics import cohen_kappa_score
import numpy as np

class IRAScorer:
    """Inter-rater agreement scoring"""

    def score(self,
              reference: List[str],
              hypothesis: List[str]) -> IRAResult:
        """Compute agreement statistics"""

        # Basic agreement
        agreements = [r == h for r, h in zip(reference, hypothesis)]
        percent_agreement = sum(agreements) / len(agreements)

        # Cohen's kappa
        kappa = cohen_kappa_score(reference, hypothesis)

        # Build confusion matrix
        labels = sorted(set(reference + hypothesis))
        confusion = self.build_confusion_matrix(
            reference, hypothesis, labels
        )

        return IRAResult(
            percent_agreement=percent_agreement,
            cohen_kappa=kappa,
            confusion_matrix=confusion,
            labels=labels
        )
```

#### Day 8: IRA Validation
```python
# tests/test_ira_parity.py
def test_ira_multiclass():
    """Test multi-class agreement metrics"""
    ref = ["seiz", "bckg", "artf", "seiz"]
    hyp = ["seiz", "artf", "artf", "bckg"]

    alpha_result = run_alpha_ira(ref, hyp)
    beta_result = run_beta_ira(ref, hyp)

    assert abs(alpha_result['kappa'] - beta_result.cohen_kappa) < 1e-10
```

### Days 9-10: Integration & Validation Suite

#### Day 9: Full Algorithm Suite
```python
# tests/test_full_suite.py
class TestFullAlgorithmSuite:
    """Comprehensive testing of all algorithms"""

    @pytest.fixture
    def test_data(self):
        return load_comprehensive_test_set()

    def test_all_algorithms_parity(self, test_data):
        """All 5 algorithms match Alpha"""
        for algorithm in ['dp', 'epoch', 'overlap', 'taes', 'ira']:
            alpha = run_alpha(test_data, algorithm)
            beta = run_beta(test_data, algorithm)

            validator = ParityValidator()
            report = validator.compare(alpha, beta)

            assert report.passed, f"{algorithm} failed parity"
```

#### Day 10: Documentation & Performance
```python
# benchmarks/test_algorithm_performance.py
def test_algorithm_performance_suite(benchmark):
    """Benchmark all algorithms"""
    results = {}

    for algorithm in ['dp', 'epoch', 'overlap', 'taes', 'ira']:
        ref = generate_events(1000)
        hyp = generate_events(1000)

        beta_time = benchmark(run_beta, ref, hyp, algorithm)
        alpha_time = time_function(run_alpha, ref, hyp, algorithm)

        results[algorithm] = {
            'beta_time': beta_time,
            'alpha_time': alpha_time,
            'speedup': alpha_time / beta_time
        }

    print_performance_table(results)
```

### Deliverables Checklist
- [ ] `nedc_bench/algorithms/dp_alignment.py` - DP implementation
- [ ] `nedc_bench/algorithms/epoch.py` - Epoch scoring
- [ ] `nedc_bench/algorithms/overlap.py` - Overlap scoring
- [ ] `nedc_bench/algorithms/ira.py` - IRA scoring
- [ ] `tests/test_*_algorithm.py` - Algorithm tests
- [ ] `tests/test_*_parity.py` - Parity tests
- [ ] `benchmarks/` - Performance tests
- [ ] `PHASE_3_CORE_ALGORITHMS.md` - Updated documentation

### Definition of Done
1. ✅ All 5 algorithms implemented under `nedc_bench/`
2. ✅ 100% test coverage on each
3. ✅ Full parity with Alpha validated
4. ✅ Performance benchmarks documented
5. ✅ Algorithm documentation complete

### Next Phase Entry Criteria
- Complete algorithm suite validated
- Ready for API layer
- Performance baselines established

---
## Notes
- Implement algorithms in order of complexity
- TAES already done, start with Epoch or DP (simpler)
- Use existing libraries (sklearn) where appropriate
- Document any algorithmic ambiguities found
- Keep numerical precision as top priority (counts-first; metrics recomputed centrally; `atol=1e-10`)

### Parity Validation Additions
- Extend `nedc_bench/validation/parity.py` with:
  - `compare_dp(alpha_dp: dict, beta_dp: dict) -> ValidationReport`
  - `compare_epoch(alpha_epoch: dict, beta_epoch: dict) -> ValidationReport`
  - `compare_overlap(alpha_overlap: dict, beta_overlap: OverlapResult) -> ValidationReport`
  - `compare_ira(alpha_ira: dict, beta_ira: IRAResult) -> ValidationReport`
- All comparisons use counts-first; recompute metrics centrally with absolute tolerance.
