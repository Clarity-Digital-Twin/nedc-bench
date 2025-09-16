# Clean Architecture Proposal for NEDC-BENCH

## Current State vs. Clean Architecture Vision

### What We're Building (Domain Understanding)

NEDC-BENCH is a **clinical-grade EEG evaluation platform** that ensures algorithmic correctness through dual-pipeline validation. The core value proposition: **"Prove your seizure detection algorithm works correctly by matching the gold standard."**

### Uncle Bob's Clean Architecture Layers Applied to NEDC-BENCH

```
┌─────────────────────────────────────────────────────────────┐
│                      External Systems                       │
│  (CLI, REST API, WebSockets, Docker, K8s)                  │
├─────────────────────────────────────────────────────────────┤
│                    Interface Adapters                       │
│  (Controllers, Presenters, Gateways)                       │
├─────────────────────────────────────────────────────────────┤
│                     Application Core                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Use Cases                        │   │
│  │  (Evaluate, Compare, Validate, Report)             │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                  Domain Entities                    │   │
│  │  (Annotation, Event, Metric, Score)                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Directory Structure

```
nedc-bench/
├── src/                          # All source code
│   ├── domain/                   # Enterprise Business Rules (Most Stable)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── annotation.py    # Core data structures
│   │   │   ├── event.py
│   │   │   ├── metric.py
│   │   │   └── score.py
│   │   ├── value_objects/
│   │   │   ├── time_range.py
│   │   │   ├── channel.py
│   │   │   └── event_type.py
│   │   └── interfaces/           # Repository & Service Interfaces
│   │       ├── scorer.py        # Abstract scorer interface
│   │       └── validator.py
│   │
│   ├── application/              # Application Business Rules
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── evaluate_annotations.py
│   │   │   ├── compare_pipelines.py
│   │   │   ├── validate_parity.py
│   │   │   └── generate_report.py
│   │   ├── services/
│   │   │   ├── orchestrator.py
│   │   │   └── job_manager.py
│   │   └── dto/                 # Data Transfer Objects
│   │       ├── evaluation_request.py
│   │       └── evaluation_response.py
│   │
│   ├── infrastructure/           # Frameworks & Drivers
│   │   ├── __init__.py
│   │   ├── scoring/             # Concrete Implementations
│   │   │   ├── native/          # Our Python implementations
│   │   │   │   ├── taes_scorer.py
│   │   │   │   ├── overlap_scorer.py
│   │   │   │   ├── epoch_scorer.py
│   │   │   │   ├── dp_scorer.py
│   │   │   │   └── ira_scorer.py
│   │   │   └── legacy/          # Wrappers around external
│   │   │       └── nedc_wrapper.py
│   │   ├── persistence/
│   │   │   ├── file_repository.py
│   │   │   └── redis_repository.py
│   │   ├── monitoring/
│   │   │   └── prometheus_metrics.py
│   │   └── external/            # Third-party integrations
│   │       └── nedc_v6/         # Vendored NEDC (untouched)
│   │
│   ├── interfaces/               # Interface Adapters
│   │   ├── __init__.py
│   │   ├── api/                 # REST API
│   │   │   ├── app.py
│   │   │   ├── routers/
│   │   │   ├── dependencies.py
│   │   │   └── middleware.py
│   │   ├── cli/                 # Command Line Interface
│   │   │   ├── __init__.py
│   │   │   ├── app.py          # Main Typer app
│   │   │   ├── commands/
│   │   │   │   ├── evaluate.py
│   │   │   │   ├── validate.py
│   │   │   │   ├── batch.py
│   │   │   │   └── report.py
│   │   │   └── formatters/      # Output formatting
│   │   └── websocket/
│   │       └── handlers.py
│   │
│   └── shared/                   # Cross-cutting concerns
│       ├── __init__.py
│       ├── config.py
│       ├── logging.py
│       ├── exceptions.py
│       └── constants.py
│
├── tests/                        # Mirrors src/ structure
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── scripts/                      # Development & maintenance scripts
│   ├── migrate.py
│   ├── benchmark.py
│   └── generate_docs.py
│
├── docs/
├── docker/
│   ├── api.Dockerfile
│   ├── worker.Dockerfile
│   └── cli.Dockerfile
├── k8s/
├── data/                        # Test data
└── pyproject.toml
```

## Key Design Decisions

### 1. Dependency Rule (Most Important!)

Dependencies only point **inward**:

- Domain knows nothing about Application/Infrastructure
- Application knows Domain but not Infrastructure
- Infrastructure knows both Domain and Application
- Interfaces know Application but implement through Infrastructure

### 2. Domain Layer (Entities & Business Logic)

```python
# src/domain/entities/annotation.py
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)  # Immutable
class Event:
    """Pure domain object - no dependencies"""

    start_time: float
    end_time: float
    event_type: str
    channel: str

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def overlaps_with(self, other: "Event") -> bool:
        """Core business logic lives here"""
        return not (
            self.end_time <= other.start_time or other.end_time <= self.start_time
        )


# src/domain/interfaces/scorer.py
class ScorerInterface(Protocol):
    """Interface - no implementation"""

    def score(self, reference: list[Event], hypothesis: list[Event]) -> Score: ...
```

### 3. Application Layer (Use Cases)

```python
# src/application/use_cases/evaluate_annotations.py
from domain.interfaces import ScorerInterface
from application.dto import EvaluationRequest, EvaluationResponse


class EvaluateAnnotationsUseCase:
    def __init__(self, scorer: ScorerInterface):
        self.scorer = scorer  # Dependency injection

    def execute(self, request: EvaluationRequest) -> EvaluationResponse:
        """Orchestrates the evaluation process"""
        # Use case specific logic
        score = self.scorer.score(request.reference, request.hypothesis)
        return EvaluationResponse(score=score)
```

### 4. Infrastructure Layer (Implementations)

```python
# src/infrastructure/scoring/native/taes_scorer.py
from domain.interfaces import ScorerInterface
from domain.entities import Event, Score


class TAESScorer:  # Implements ScorerInterface
    def score(self, reference: list[Event], hypothesis: list[Event]) -> Score:
        """Concrete implementation"""
        # Actual TAES algorithm
        return Score(...)
```

### 5. Interface Layer (CLI/API)

```python
# src/interfaces/cli/commands/evaluate.py
import typer
from application.use_cases import EvaluateAnnotationsUseCase
from infrastructure.scoring.native import TAESScorer

app = typer.Typer()


@app.command()
def evaluate(
    reference: Path = typer.Argument(...),
    hypothesis: Path = typer.Argument(...),
    algorithm: str = typer.Option("taes"),
):
    """Clean CLI interface"""
    # Dependency injection at the edge
    scorer = TAESScorer() if algorithm == "taes" else ...
    use_case = EvaluateAnnotationsUseCase(scorer)

    result = use_case.execute(...)
    print(result)
```

## Migration Strategy

### Phase 1: Create Domain Layer (No Breaking Changes)

1. Extract pure entities from current models
1. Define interfaces for scorers
1. Create value objects

### Phase 2: Build Application Layer

1. Extract use cases from current orchestration
1. Create DTOs for boundaries
1. Implement service interfaces

### Phase 3: Refactor Infrastructure

1. Move scorers to infrastructure/scoring
1. Move alpha wrapper to infrastructure/scoring/legacy
1. Keep nedc_eeg_eval as infrastructure/external

### Phase 4: Clean Interfaces

1. Create unified CLI with Typer
1. Refactor API to use use cases
1. Add WebSocket support

### Phase 5: Complete Testing Pyramid

1. Unit tests for domain (no dependencies)
1. Integration tests for infrastructure
1. E2E tests through interfaces

## Benefits of This Architecture

### 1. Testability

- Domain logic testable without any dependencies
- Use cases testable with mock interfaces
- Clear boundaries for integration tests

### 2. Flexibility

- Easy to add new scoring algorithms (just implement interface)
- Can swap infrastructure without touching domain
- Multiple interfaces (CLI, API, WebSocket) share same core

### 3. Maintainability

- Clear separation of concerns
- Business logic isolated from frameworks
- Easy to understand data flow

### 4. Scalability

- Can split into microservices along boundaries
- Domain remains stable as infrastructure evolves
- Clear async boundaries for performance

## Example: Adding a New Scoring Algorithm

With clean architecture, adding a new scorer requires:

1. **Implement the interface** (infrastructure layer):

```python
# src/infrastructure/scoring/native/new_scorer.py
class NewScorer:  # Implements ScorerInterface
    def score(self, ref, hyp) -> Score:
        # Implementation
```

2. **Register in dependency injection**:

```python
# src/interfaces/cli/dependencies.py
SCORERS = {
    "taes": TAESScorer,
    "new": NewScorer,  # One line addition
}
```

That's it! No changes to domain, application, or other scorers.

## CLI Design Following Clean Architecture

```bash
# Main command group
nedc-bench --help

# Evaluation commands
nedc-bench evaluate <ref> <hyp> --algorithm taes --format json
nedc-bench evaluate-batch <list-file> --output results/
nedc-bench evaluate-dual <ref> <hyp> --validate-parity

# Validation commands
nedc-bench validate parity <alpha-result> <beta-result>
nedc-bench validate metrics <result> --threshold 0.95

# Reporting commands
nedc-bench report generate <results-dir> --format html
nedc-bench report compare <result1> <result2>

# Pipeline commands
nedc-bench pipeline run <config.yaml>
nedc-bench pipeline status <job-id>

# Development commands
nedc-bench dev benchmark --iterations 100
nedc-bench dev profile <ref> <hyp>
```

## The Payoff

When done right, this structure means:

- **New developer onboarding**: "Start with domain/ to understand what we do"
- **Adding features**: "Implement interface, wire in dependency injection"
- **Testing**: "Test domain without mocks, test infrastructure with real files"
- **Debugging**: "Follow the use case from interface → application → domain"
- **Performance**: "Profile infrastructure, optimize without touching domain"

## Next Steps

1. **Decide on migration approach**:

   - Big bang: Full restructure in feature branch
   - Incremental: Gradual refactoring maintaining compatibility

1. **Start with highest value**:

   - CLI interface (immediate user value)
   - Domain extraction (enables unit testing)
   - Use case layer (clarifies business logic)

1. **Maintain backwards compatibility**:

   - Keep current imports working via __init__.py
   - Deprecate gradually
   - Document migration path

This is how professionals building production systems think about code organization. It's not about fewer directories or shorter imports - it's about **sustainable architecture that preserves business logic while allowing technical evolution**.

What matters is that changes in FastAPI don't break our scoring algorithms, changes in scoring algorithms don't break our CLI, and new features don't require modifying stable code.

That's Clean Architecture. That's what Uncle Bob would do.
