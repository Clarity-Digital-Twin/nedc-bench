# Architecture Comparison: Current vs Clean

## Current Structure Pain Points

### 1. Mixed Responsibilities

```python
# nedc_bench/api/main.py - Does too much!
- FastAPI setup
- Business logic
- Job orchestration
- Database access
- Metrics collection
```

### 2. Tight Coupling

```python
# Scripts directly import from everywhere
from nedc_bench.algorithms.taes import TAESScorer  # Direct implementation dependency
from alpha.wrapper import NEDCAlphaWrapper  # Direct wrapper dependency

# Hard to test, hard to mock, hard to swap
```

### 3. No Clear Boundaries

- Where does business logic live? (scattered across algorithms/, orchestration/, api/)
- Where do I add a new scorer? (algorithms? but alpha is separate?)
- What depends on what? (everything imports everything)

## Clean Architecture Solutions

### 1. Single Responsibility

```python
# Each layer has ONE job:
domain/         # What is a seizure event? How do we score?
application/    # How do we evaluate files? What's the workflow?
infrastructure/ # How do we read files? Call NEDC? Store results?
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

### Current Architecture (Pain!)

```python
# Have to modify existing code:
# 1. Edit nedc_bench/algorithms/taes.py to add GPU option
# 2. Update api/main.py to handle GPU flag
# 3. Change orchestration/executor.py for GPU scheduling
# 4. Update every script that uses TAES
# 5. Risk breaking existing functionality
```

### Clean Architecture (Easy!)

```python
# 1. Add new implementation:
# src/infrastructure/scoring/gpu/taes_gpu_scorer.py
class TAESGPUScorer(ScorerInterface):
    def score(self, ref, hyp):
        # GPU implementation

# 2. Register in DI container:
SCORERS['taes-gpu'] = TAESGPUScorer

# Done! No existing code modified!
```

## Testing Comparison

### Current Testing (Coupled)

```python
def test_taes_scorer():
    # Need real files!
    with TemporaryDirectory() as tmpdir:
        # Write test files
        create_csv_bi_file(tmpdir / "ref.csv_bi")
        create_csv_bi_file(tmpdir / "hyp.csv_bi")

        # Test is slow, brittle, complex
        scorer = TAESScorer()
        result = scorer.score_files(...)  # I/O in unit test!
```

### Clean Testing (Isolated)

```python
def test_taes_algorithm():
    # Pure domain logic, no I/O!
    ref_events = [Event(0, 10, "SEIZ"), Event(20, 30, "SEIZ")]
    hyp_events = [Event(5, 15, "SEIZ")]

    scorer = TAESAlgorithm()  # Pure algorithm, no dependencies
    score = scorer.calculate(ref_events, hyp_events)

    # Fast, deterministic, easy to understand
    assert score.sensitivity == 0.75
```

## Onboarding Comparison

### New Developer Joins Team

**Current Structure Journey:**

1. "Where do I start?"
1. Opens `nedc_bench/` - "Is this everything?"
1. Sees `alpha/` - "What's this? Another implementation?"
1. Finds `scripts/` - "Are these the entry points?"
1. Discovers business logic scattered across 5 directories
1. "How do I run this?" - No clear CLI
1. "How do I test my changes?" - Tests coupled to infrastructure

**Clean Architecture Journey:**

1. "Where do I start?" → `src/domain/` - "Ah, these are the core concepts"
1. "How does evaluation work?" → `src/application/use_cases/evaluate.py`
1. "How do I run this?" → `nedc-bench --help` - Beautiful CLI
1. "Where's the TAES implementation?" → `src/infrastructure/scoring/native/taes.py`
1. "How do I test?" → Pure domain logic needs no mocks
1. Clear mental model in 30 minutes

## Performance & Scaling

### Current Monolithic Coupling

```
Everything depends on everything
Can't parallelize without complex locking
Can't split into services without major refactor
```

### Clean Architecture Scaling

```
# Easy to split along boundaries:

[Domain Service]     # Core scoring algorithms (CPU intensive)
    ↕️ gRPC
[Application Service] # Orchestration (I/O intensive)
    ↕️ REST
[API Gateway]        # User interfaces (Connection intensive)

# Or run as monolith - same code!
```

## The Business Case

### Current Architecture Costs

- **Bug fix time**: 2-3 hours (finding where logic lives)
- **New feature**: 2-3 days (modifying existing code)
- **New scorer**: 1 week (understanding all dependencies)
- **Onboarding**: 2 weeks (mental model unclear)
- **Test coverage**: ~70% (hard to test coupled code)

### Clean Architecture Benefits

- **Bug fix time**: 30 mins (clear boundaries)
- **New feature**: 4 hours (implement interface)
- **New scorer**: 2 hours (just implement interface)
- **Onboarding**: 2 days (clear structure)
- **Test coverage**: ~95% (easy to test pure functions)

## But What About YAGNI?

"You Aren't Gonna Need It" - fair point! But we ALREADY need:

- Multiple scoring algorithms (TAES, Overlap, Epoch, DP, IRA)
- Multiple interfaces (API, CLI, potentially GUI)
- Multiple pipelines (Alpha, Beta, dual validation)
- Parity validation (complex business logic)
- Job orchestration (async processing)

This isn't overengineering - it's organizing complexity we already have!

## Migration Path (Pragmatic)

We don't need to rewrite everything! Start with:

### Week 1: CLI Interface

```bash
# Add simple CLI wrapper around existing code
nedc-bench evaluate ref.csv hyp.csv --algorithm taes
# Immediate user value, no restructuring needed
```

### Week 2: Extract Domain

```python
# Pull out pure data classes
src / domain / entities / event.py  # Just the data structure
# Can coexist with current code
```

### Week 3: Create Use Cases

```python
# Wrap existing orchestration
src / application / use_cases / evaluate.py
# Calls existing code, provides clean interface
```

### Week 4: Gradual Infrastructure Move

```python
# Move scorers one at a time
# Old imports still work via compatibility layer
```

## The Bottom Line

**Current Architecture:**

- Works, but hard to change
- Couples business logic to infrastructure
- Testing requires complex setup
- Onboarding is painful

**Clean Architecture:**

- Business logic protected from change
- Easy to test, easy to extend
- Clear mental model
- Professional-grade codebase

It's the difference between "code that works" and "code that works AND can evolve."
