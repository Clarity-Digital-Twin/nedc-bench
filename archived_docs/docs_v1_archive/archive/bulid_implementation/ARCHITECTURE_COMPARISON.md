# Architecture Comparison: Current vs Clean

Note on repo reality

- This document describes a target “clean architecture” direction. For the current refactor we will only move `nedc_bench/` into `src/` with no import changes. Domain/application layering can be introduced incrementally after the src move.

## Current Structure Pain Points

### 1. Mixed Responsibilities

```python
# nedc_bench/api/main.py - Does too much
- FastAPI setup
- Routers wiring
- Background worker orchestration
- Metrics/CORS middleware
```

### 2. Tight Coupling

```python
# Scripts directly import from concrete implementations
from nedc_bench.algorithms.taes import TAESScorer  # Direct implementation dependency
from alpha.wrapper import NEDCAlphaWrapper  # Direct wrapper dependency

# Hard to test, hard to mock, hard to swap
```

### 3. Unclear Boundaries

- Business logic and orchestration are interleaved across `algorithms/`, `orchestration/`, and `api/`
- Adding a new scorer means touching multiple layers
- Dependencies between modules are not explicit via interfaces

## Clean Architecture Solutions

### 1. Single Responsibility

```python
# Each layer has ONE job:
domain/         # What is a seizure event? How do we score?
application/    # How do we evaluate files? What's the workflow?
infrastructure/ # How do we read files? Call NEDC? Store/cache results?
interfaces/     # How does user interact? CLI? API? WebSocket?
```

### 2. Dependency Inversion

```python
# Old way (tight coupling):
class TAESScorer:
    def __init__(self):
        self.file_reader = CSVBIReader()  # Hard dependency!


# Clean way (loose coupling):
class TAESScorer:
    def __init__(self, reader: ReaderInterface):  # Inject dependency!
        self.reader = reader
```

### 3. Clear Boundaries via Interfaces

```python
# Domain defines the contract:
class ScorerInterface(Protocol):
    def score(self, ref: list[Event], hyp: list[Event]) -> Score: ...


# Infrastructure provides implementations:
class NEDCScorer(ScorerInterface): ...


class NativeScorer(ScorerInterface): ...


class GPUScorer(ScorerInterface): ...  # Easy to add!
```

## Real-World Example: Adding GPU Acceleration

### Current Architecture (Pain)

```python
# Must modify multiple places:
# 1. Edit nedc_bench/algorithms/taes.py to add GPU
# 2. Update API wiring to pass GPU flag
# 3. Change orchestrator for scheduling
# 4. Update scripts using TAES
# 5. Risk breaking existing functionality
```

### Clean Architecture (Straightforward)

```python
# 1. Add new implementation:
# src/infrastructure/scoring/gpu/taes_gpu_scorer.py
class TAESGPUScorer(ScorerInterface):
    def score(self, ref, hyp):
        # GPU implementation

# 2. Register in DI container:
SCORERS['taes-gpu'] = TAESGPUScorer
```

## Testing Comparison

### Current Testing (Coupled)

```python
def test_taes_scorer():
    # Need real files
    with TemporaryDirectory() as tmpdir:
        create_csv_bi_file(tmpdir / "ref.csv_bi")
        create_csv_bi_file(tmpdir / "hyp.csv_bi")

        scorer = TAESScorer()
        result = scorer.score_files(...)
```

### Clean Testing (Isolated)

```python
def test_taes_algorithm():
    ref_events = [Event(0, 10, "SEIZ"), Event(20, 30, "SEIZ")]
    hyp_events = [Event(5, 15, "SEIZ")]

    scorer = TAESAlgorithm()  # Pure algorithm, no dependencies
    score = scorer.calculate(ref_events, hyp_events)

    assert score.sensitivity == 0.75
```

## Onboarding Comparison

### Current

- “Where do I start?” — `nedc_bench/` vs `alpha/` is not obvious
- Scripts import concrete implementations
- Tests mix orchestration and infrastructure

### Clean

- Start with `domain/` to understand core concepts
- Use cases in `application/` show workflows
- Infrastructure implements interfaces
- CLI/API are just adapters

## Performance & Scaling

### Current Monolithic Coupling

```
Tighter coupling makes parallelism and service extraction harder
```

### Clean Architecture Scaling

```
[Domain Service]     # Core scoring algorithms (CPU intensive)
    ↕️ gRPC
[Application Service] # Orchestration (I/O intensive)
    ↕️ REST
[API Gateway]        # User interfaces (Connection intensive)
```

## The Business Case

- Faster bug fixes through clearer boundaries
- Lower risk when adding algorithms and features
- Easier onboarding via a clean mental model

## Migration Path (Pragmatic)

- Phase 0 (now): Move `nedc_bench` to `src/` (no import changes)
- Phase 1: Extract domain entities incrementally
- Phase 2: Introduce use cases layer around current orchestrator
- Phase 3: Move scorers behind interfaces
- Phase 4: Adopt DI wiring for CLI/API

## Bottom Line

The current code works, but a layered architecture improves testability, extensibility, and onboarding. Start small (src/ move), then incrementally introduce the layers.
