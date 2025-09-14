# Phase 2: First Algorithm - TAES with Parity Testing
## Vertical Slice Goal: Beta TAES Implementation with Dual-Pipeline Validation

### Duration: 5 Days

### Success Criteria (TDD)
- [ ] Beta TAES algorithm implemented with full type hints
- [ ] Parity validator compares Alpha vs Beta results
- [ ] 100% test coverage on Beta TAES
- [ ] Numerical accuracy within 1e-10
- [ ] Performance benchmarks established

### Day 1: Data Models & Types

#### Morning: Pydantic Models
```python
# tests/test_models.py
def test_event_annotation_validation():
    """Test event annotation validation"""
    # Valid annotation
    event = EventAnnotation(
        channel="TERM",
        start_time=0.0,
        stop_time=10.0,
        label="seiz",
        confidence=1.0
    )
    assert event.duration == 10.0

    # Invalid: stop < start
    with pytest.raises(ValidationError):
        EventAnnotation(start_time=10.0, stop_time=5.0)
```

#### Afternoon: Type-Safe Structures
```python
# beta/src/models/annotations.py
from pydantic import BaseModel, Field, validator
from typing import Literal, List

class EventAnnotation(BaseModel):
    channel: Literal["TERM"] = "TERM"
    start_time: float = Field(ge=0)
    stop_time: float = Field(gt=0)
    label: str
    confidence: float = Field(ge=0, le=1)

    @property
    def duration(self) -> float:
        return self.stop_time - self.start_time

    @validator('stop_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('stop_time must be > start_time')
        return v
```

### Day 2: TAES Algorithm Implementation

#### Morning: Core Algorithm
```python
# tests/test_taes_algorithm.py
def test_taes_exact_match():
    """Perfect match should give perfect scores"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz")]
    hyp = [EventAnnotation(start_time=0, stop_time=10, label="seiz")]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.sensitivity == 1.0
    assert result.precision == 1.0
    assert result.f1_score == 1.0
```

#### Afternoon: Edge Cases
```python
# beta/src/algorithms/taes.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TAESResult:
    true_positives: int
    false_positives: int
    false_negatives: int
    sensitivity: float
    precision: float
    f1_score: float

class TAESScorer:
    """Time-Aligned Event Scoring implementation"""

    def score(self,
              reference: List[EventAnnotation],
              hypothesis: List[EventAnnotation]) -> TAESResult:
        """
        Score hypothesis against reference using TAES algorithm.
        Implements exact algorithm from Shah et al. 2021.
        """
        tp, fp, fn = self._compute_confusion(reference, hypothesis)

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * (precision * sensitivity) / (precision + sensitivity) \
             if (precision + sensitivity) > 0 else 0.0

        return TAESResult(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            sensitivity=sensitivity,
            precision=precision,
            f1_score=f1
        )
```

### Day 3: Parity Validator

#### Morning: Comparison Framework
```python
# tests/test_parity_validator.py
def test_parity_exact_match():
    """Alpha and Beta produce identical results"""
    test_data = load_golden_test()

    alpha_result = run_alpha_taes(test_data)
    beta_result = run_beta_taes(test_data)

    validator = ParityValidator(tolerance=1e-10)
    report = validator.compare(alpha_result, beta_result)

    assert report.passed
    assert len(report.discrepancies) == 0
```

#### Afternoon: Discrepancy Detection
```python
# validator/parity.py
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class DiscrepancyReport:
    metric: str
    alpha_value: float
    beta_value: float
    difference: float
    tolerance: float

class ParityValidator:
    def __init__(self, tolerance: float = 1e-10):
        self.tolerance = tolerance

    def compare(self, alpha: Dict, beta: Dict) -> ValidationReport:
        """Compare Alpha and Beta results"""
        discrepancies = []

        for key in alpha.keys():
            if key not in beta:
                discrepancies.append(f"Missing key: {key}")
                continue

            if isinstance(alpha[key], float):
                if not np.isclose(alpha[key], beta[key], rtol=self.tolerance):
                    discrepancies.append(DiscrepancyReport(
                        metric=key,
                        alpha_value=alpha[key],
                        beta_value=beta[key],
                        difference=abs(alpha[key] - beta[key]),
                        tolerance=self.tolerance
                    ))

        return ValidationReport(
            passed=len(discrepancies) == 0,
            discrepancies=discrepancies
        )
```

### Day 4: Dual Pipeline Integration

#### Morning: Orchestrator
```python
# tests/test_dual_pipeline.py
@pytest.mark.integration
def test_dual_pipeline_taes():
    """Run both pipelines and validate parity"""
    orchestrator = DualPipelineOrchestrator()

    result = orchestrator.evaluate(
        ref_file="tests/data/ref.csv_bi",
        hyp_file="tests/data/hyp.csv_bi",
        algorithm="taes"
    )

    assert result.alpha_result is not None
    assert result.beta_result is not None
    assert result.parity_passed
```

#### Afternoon: Parallel Execution
```python
# orchestrator/dual_pipeline.py
import asyncio
from typing import Tuple

class DualPipelineOrchestrator:
    def __init__(self):
        self.alpha = AlphaPipeline()
        self.beta = BetaPipeline()
        self.validator = ParityValidator()

    async def evaluate_async(self, ref, hyp, algorithm="taes"):
        """Run both pipelines in parallel"""
        alpha_task = asyncio.create_task(
            self.alpha.run_async(ref, hyp, algorithm)
        )
        beta_task = asyncio.create_task(
            self.beta.run_async(ref, hyp, algorithm)
        )

        alpha_result, beta_result = await asyncio.gather(
            alpha_task, beta_task
        )

        parity = self.validator.compare(alpha_result, beta_result)

        return DualResult(
            alpha_result=alpha_result,
            beta_result=beta_result,
            parity_report=parity,
            parity_passed=parity.passed
        )
```

### Day 5: Performance & Documentation

#### Morning: Performance Benchmarks
```python
# tests/test_performance.py
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

def test_taes_performance(benchmark: BenchmarkFixture):
    """Beta TAES should be faster than Alpha"""
    ref = generate_events(1000)
    hyp = generate_events(1000)

    # Benchmark Beta
    beta_time = benchmark(beta_taes.score, ref, hyp)

    # Run Alpha for comparison
    alpha_time = time_function(alpha_taes.score, ref, hyp)

    # Beta should be at least as fast
    assert benchmark.stats['mean'] <= alpha_time
    # And ideally faster
    print(f"Speedup: {alpha_time / benchmark.stats['mean']:.2f}x")
```

#### Afternoon: Algorithm Documentation
```python
# docs/algorithms/taes.md
"""
# TAES Algorithm Specification

## Mathematical Foundation
TAES (Time-Aligned Event Scoring) computes:
- True Positives: Events correctly detected
- False Positives: Events incorrectly detected
- False Negatives: Events missed

## Implementation Notes
- Exact match: Events must overlap > 50%
- Time tolerance: 0.001 seconds
- Label matching: Case-sensitive

## Validation
Beta implementation validated against:
- Original NEDC v6.0.0
- Test cases from Shah et al. 2021
- 1000 synthetic test cases
"""
```

### Deliverables Checklist
- [ ] `beta/src/models/annotations.py` - Data models
- [ ] `beta/src/algorithms/taes.py` - TAES implementation
- [ ] `validator/parity.py` - Parity validator
- [ ] `orchestrator/dual_pipeline.py` - Dual execution
- [ ] `tests/test_taes_*.py` - Comprehensive tests
- [ ] `docs/algorithms/taes.md` - Documentation

### Definition of Done
1. ✅ Beta TAES fully implemented
2. ✅ 100% test coverage
3. ✅ Parity with Alpha validated
4. ✅ Performance benchmarked
5. ✅ Documentation complete

### Next Phase Entry Criteria
- TAES parity proven
- Validation framework working
- Ready for remaining 4 algorithms

---
## Notes
- Start with simplest algorithm (TAES)
- Focus on exact numerical match
- Document any algorithmic ambiguities
- Keep performance secondary to correctness