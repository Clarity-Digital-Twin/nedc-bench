# NEDC-BENCH: Modern EEG Benchmarking Platform

## Dual-Pipeline Implementation Plan

### Current Status (September 2025)

**Repository State**: Initial setup phase

- ✅ Original NEDC v6.0.0 tool vendored and functional (18,981 lines of Python)
- ✅ Basic wrapper script (`run_nedc.sh`) created and tested
- ✅ Python 3.9+ compatibility via tomllib/tomli try/except fallback
- ✅ Test data available (30 file pairs in CSV_BI format)
- ✅ Sample outputs for validation (test/results/)
- ⬜ Docker containerization not started
- ⬜ Modern pipeline (Beta) not started
- ⬜ CI/CD not configured

**Next Steps**: Ready for Phase 1 implementation

### Vision Statement

Transform the NEDC EEG Evaluation tool (v6.0.0) into **NEDC-BENCH**, a modern, production-ready benchmarking platform for EEG analysis systems while maintaining 100% algorithmic fidelity to the original Temple University implementation through continuous dual-pipeline validation.

### Core Strategy: Dual-Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NEDC-BENCH Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   Pipeline Alpha      │    │   Pipeline Beta       │      │
│  │  (Legacy Wrapper)     │    │  (Modern Rewrite)     │      │
│  ├──────────────────────┤    ├──────────────────────┤      │
│  │ • Original NEDC code  │    │ • Clean architecture  │      │
│  │ • Minimal wrapper     │    │ • Type-safe Python    │      │
│  │ • Docker container    │    │ • Async/parallel      │      │
│  │ • 100% fidelity       │    │ • Cloud-native        │      │
│  └──────────────────────┘    └──────────────────────┘      │
│             ↓                           ↓                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Unified API & Result Validator          │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Foundation (Week 1) - 5 Days

### 1.1 Repository Setup

```yaml
nedc-bench/  # Target structure after Phase 1 scaffolding
├── nedc_eeg_eval/                # Vendored original tool (KEEP AS IS)
│   └── v6.0.0/                   # Original NEDC code - DO NOT MODIFY
├── .github/
│   ├── workflows/
│   │   ├── alpha-pipeline.yml    # Legacy tests
│   │   ├── beta-pipeline.yml     # Modern tests
│   │   └── validation.yml        # Cross-validation
│   └── ISSUE_TEMPLATE/
├── alpha/                         # Pipeline Alpha (Legacy Wrapper)
│   ├── wrapper/                  # Python wrapper for text parsing
│   ├── Dockerfile                # Python 3.9+ container
│   └── requirements.txt          # numpy, scipy, lxml, tomli
├── beta/                          # Pipeline Beta (Modern)
│   ├── src/
│   │   ├── algorithms/           # Clean implementations of 5 algorithms
│   │   ├── models/               # Pydantic models for type safety
│   │   ├── api/                  # FastAPI endpoints
│   │   └── cli/                  # Click-based CLI
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile                # Multi-stage optimized
│   └── pyproject.toml            # Modern Python packaging
├── validator/                     # Cross-validation suite
│   ├── golden_tests/             # Test cases from NEDC paper
│   ├── comparator.py             # Alpha vs Beta comparison
│   └── reports/                  # Parity validation reports
├── docs/
│   ├── api/                      # OpenAPI documentation
│   ├── algorithms/               # Mathematical specifications
│   └── migration/                # Migration guide
└── docker-compose.yml            # Full stack deployment
```

### 1.2 Pipeline Alpha (Legacy Wrapper)

#### Minimal Intervention Strategy

```python
# alpha/wrapper/nedc_wrapper.py
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List


class NEDCAlphaWrapper:
    """Wrapper around original NEDC v6.0.0 code"""

    def __init__(self, nedc_root: Path = Path("/opt/nedc")):
        self.nedc_root = nedc_root
        os.environ["NEDC_NFC"] = str(self.nedc_root)
        os.environ["PYTHONPATH"] = (
            f"{self.nedc_root}/lib:{os.environ.get('PYTHONPATH', '')}"
        )
        self._validate_environment()

    def evaluate(self, ref_list: str, hyp_list: str) -> Dict:
        """Run NEDC evaluation and parse text output to JSON"""
        cmd = [
            "python",
            str(self.nedc_root / "bin" / "nedc_eeg_eval"),
            ref_list,
            hyp_list,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse the 5 algorithm outputs from text
        return self._parse_all_outputs(result.stdout)

    def _parse_output(self, text: str) -> Dict:
        """Convert text output to structured format"""
        # Regex parsing of summary.txt
        return parsed_results
```

#### Dockerization

```dockerfile
# alpha/Dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

# Copy the vendored NEDC tool
COPY nedc_eeg_eval/v6.0.0/ /opt/nedc/
COPY alpha/wrapper/ /app/

# Install Python dependencies
RUN pip install numpy==2.0.2 scipy==1.14.1 lxml==5.3.0 tomli==2.0.1

# Set required environment variables
ENV NEDC_NFC=/opt/nedc
ENV PYTHONPATH=/opt/nedc/lib:$PYTHONPATH

WORKDIR /app
CMD ["python", "nedc_wrapper.py"]
```

## Phase 2: First Algorithm - TAES (Week 2) - 5 Days

### 2.1 Beta Pipeline - Modern Implementation of 5 Algorithms

#### Core Design Principles

1. **Type Safety**: Full type hints with mypy strict mode
1. **Async First**: AsyncIO for parallel processing
1. **Exact Fidelity**: Identical numerical results to Alpha
1. **100% Test Coverage**: Every algorithm fully tested
1. **Continuous Validation**: Dual pipeline comparison on every run

#### Algorithm Modules

```python
# beta/src/algorithms/base.py
from abc import ABC, abstractmethod
from typing import Protocol, Generic, TypeVar
import numpy.typing as npt

T = TypeVar("T", bound="Annotation")


class ScoringAlgorithm(Protocol[T]):
    """Protocol for all scoring algorithms"""

    @abstractmethod
    async def score(self, reference: List[T], hypothesis: List[T]) -> ScoringResult: ...


# beta/src/algorithms/taes.py
@dataclass
class TAESConfig:
    """Type-safe configuration"""

    guard_width: float = 0.001
    round_digits: int = 3


class TAESScorer(ScoringAlgorithm[EventAnnotation]):
    """Modern TAES implementation"""

    def __init__(self, config: TAESConfig):
        self.config = config

    async def score(
        self, reference: List[EventAnnotation], hypothesis: List[EventAnnotation]
    ) -> TAESResult:
        # Exact algorithm from original
        # But with modern Python patterns
        ...
```

#### Data Models (Pydantic)

```python
# beta/src/models/annotations.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Literal


class EventAnnotation(BaseModel):
    """Validated event annotation"""

    channel: Literal["TERM"] = "TERM"
    start_time: float = Field(ge=0)
    stop_time: float = Field(gt=0)
    label: str
    confidence: float = Field(ge=0, le=1)

    @validator("stop_time")
    def validate_times(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("stop_time must be > start_time")
        return v


class ScoringResult(BaseModel):
    """Structured scoring output"""

    algorithm: str
    timestamp: datetime
    metrics: MetricsDict
    confusion_matrix: npt.NDArray[np.int32]
    per_file_results: List[FileResult]
```

### 2.2 API Layer

#### FastAPI Implementation

```python
# beta/src/api/main.py
from fastapi import FastAPI, UploadFile, BackgroundTasks
from typing import List
import uuid

app = FastAPI(title="NEDC-BENCH API", version="2.0.0")


@app.post("/evaluate/")
async def evaluate(
    reference: UploadFile,
    hypothesis: UploadFile,
    algorithms: List[str] = Query(default=["all"]),
    background_tasks: BackgroundTasks,
) -> EvaluationResponse:
    """Async evaluation endpoint"""
    job_id = uuid.uuid4()
    background_tasks.add_task(run_evaluation, job_id, reference, hypothesis)
    return {"job_id": job_id, "status": "processing"}


@app.get("/results/{job_id}")
async def get_results(job_id: UUID) -> ResultsResponse:
    """Retrieve evaluation results"""
    ...


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: UUID):
    """Real-time progress updates"""
    ...
```

## Phase 3: Core Algorithms (Weeks 3-4) - 10 Days

### 3.1 Cross-Validation Suite

#### Automated Testing

```python
# validator/comparator.py
import numpy as np
from typing import Tuple


class ResultValidator:
    """Ensures both pipelines produce identical results"""

    TOLERANCE = 1e-10  # Numerical tolerance

    async def validate_pipelines(self, dataset: TestDataset) -> ValidationReport:
        # Run both pipelines
        alpha_results = await self.run_alpha(dataset)
        beta_results = await self.run_beta(dataset)

        # Compare results
        return self.compare_results(alpha_results, beta_results)

    def compare_results(self, alpha: Dict, beta: Dict) -> ValidationReport:
        """Deep comparison with tolerance for floating point"""
        discrepancies = []

        for metric, alpha_val in alpha["metrics"].items():
            beta_val = beta["metrics"][metric]
            if not np.allclose(alpha_val, beta_val, rtol=self.TOLERANCE):
                discrepancies.append(
                    {
                        "metric": metric,
                        "alpha": alpha_val,
                        "beta": beta_val,
                        "diff": abs(alpha_val - beta_val),
                    }
                )

        return ValidationReport(
            passed=len(discrepancies) == 0, discrepancies=discrepancies
        )
```

### 3.2 Test Datasets

#### Synthetic Data Generation

```python
# validator/datasets/generator.py
class SyntheticEEGGenerator:
    """Generate test cases with known ground truth"""

    def generate_perfect_match(self) -> Tuple[List, List]:
        """Reference and hypothesis are identical"""

    def generate_no_overlap(self) -> Tuple[List, List]:
        """No events match"""

    def generate_partial_overlap(self, overlap: float) -> Tuple[List, List]:
        """Controlled overlap percentage"""

    def generate_edge_cases(self) -> List[Tuple[List, List]]:
        """Boundary conditions and edge cases"""
```

## Phase 4: API Layer (Week 5) - 5 Days

### 4.1 Parallelization

#### Multi-file Processing

```python
# beta/src/processing/parallel.py
import asyncio
from concurrent.futures import ProcessPoolExecutor


class ParallelProcessor:
    """Process multiple file pairs in parallel"""

    def __init__(self, max_workers: int = None):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    async def process_batch(
        self, file_pairs: List[Tuple[Path, Path]], algorithm: ScoringAlgorithm
    ) -> List[ScoringResult]:
        """Process file pairs in parallel"""

        loop = asyncio.get_event_loop()
        tasks = []

        for ref, hyp in file_pairs:
            task = loop.run_in_executor(
                self.executor, self._process_single, ref, hyp, algorithm
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)
```

### 4.2 Caching Layer

#### Redis Integration

```python
# beta/src/cache/redis_cache.py
import redis
import hashlib
import pickle


class ResultCache:
    """Cache evaluation results"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get_cache_key(self, ref: Path, hyp: Path, algo: str) -> str:
        """Generate deterministic cache key"""
        content = f"{ref.read_bytes()}{hyp.read_bytes()}{algo}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_or_compute(
        self, ref: Path, hyp: Path, algorithm: ScoringAlgorithm
    ) -> ScoringResult:
        """Check cache before computing"""
        key = self.get_cache_key(ref, hyp, algorithm.name)

        # Check cache
        cached = self.redis.get(key)
        if cached:
            return pickle.loads(cached)

        # Compute and cache
        result = await algorithm.score(ref, hyp)
        self.redis.set(key, pickle.dumps(result), ex=3600)
        return result
```

## Phase 5: Production Deployment (Week 6) - 5 Days

### 5.1 Kubernetes Deployment

#### Helm Chart

```yaml
# helm/nedc-bench/values.yaml
replicaCount: 3

image:
  alpha:
    repository: nedc-bench/alpha
    tag: "1.0.0"
  beta:
    repository: nedc-bench/beta
    tag: "2.0.0"

service:
  type: LoadBalancer
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
  hosts:
    - host: api.nedc-bench.io
      paths:
        - path: /
          pathType: Prefix

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

### 5.2 Observability

#### OpenTelemetry Integration

```python
# beta/src/telemetry/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc import trace_exporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(service_name: str, otlp_endpoint: str):
    """Configure distributed tracing"""

    provider = TracerProvider()
    processor = BatchSpanProcessor(
        trace_exporter.OTLPSpanExporter(endpoint=otlp_endpoint)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


# Usage in algorithms
tracer = setup_tracing("nedc-bench", "otel-collector:4317")


class TAESScorer:
    @tracer.start_as_current_span("taes_scoring")
    async def score(self, ref, hyp):
        span = trace.get_current_span()
        span.set_attribute("ref.count", len(ref))
        span.set_attribute("hyp.count", len(hyp))
        # ... algorithm implementation
```

## Summary: 30 Days Total (6 Weeks)

### 6.1 Migration Tools

#### Data Migration Script

```python
# tools/migrate.py
import click
from pathlib import Path


@click.command()
@click.option("--format", type=click.Choice(["csv_bi", "json", "parquet"]))
@click.argument("input_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
def migrate(format: str, input_dir: Path, output_dir: Path):
    """Convert legacy formats to modern formats"""

    converter = FormatConverter(format)

    for old_file in Path(input_dir).glob("*.csv_bi"):
        new_file = output_dir / f"{old_file.stem}.{format}"
        converter.convert(old_file, new_file)
        click.echo(f"Converted {old_file} -> {new_file}")
```

### 6.2 Deprecation Strategy

#### Gradual Transition Plan

1. **v2.0**: Both pipelines active, Alpha as default
1. **v2.1**: Beta as default, Alpha available via flag
1. **v2.2**: Alpha requires explicit opt-in
1. **v3.0**: Alpha removed, Beta becomes sole implementation

## Testing Strategy

### Unit Tests

```python
# beta/tests/test_algorithms.py
import pytest
from hypothesis import given, strategies as st
import numpy as np


class TestTAESScorer:
    @given(
        events=st.lists(
            st.tuples(
                st.floats(min_value=0, max_value=1000),
                st.floats(min_value=0, max_value=1000),
            )
        )
    )
    def test_property_based(self, events):
        """Property-based testing with Hypothesis"""
        # Properties that must always hold

    @pytest.mark.parametrize(
        "ref,hyp,expected",
        [
            # Edge cases from original test suite
        ],
    )
    def test_compatibility(self, ref, hyp, expected):
        """Ensure compatibility with original implementation"""
```

### Integration Tests

```python
# tests/integration/test_pipelines.py
@pytest.mark.integration
async def test_pipeline_consistency():
    """Both pipelines produce identical results"""
    dataset = load_test_dataset()

    alpha_result = await run_alpha_pipeline(dataset)
    beta_result = await run_beta_pipeline(dataset)

    assert_results_equal(alpha_result, beta_result, tolerance=1e-10)
```

### Performance Benchmarks

```python
# benchmarks/performance.py
import pytest


@pytest.mark.benchmark
def test_taes_performance(benchmark):
    """Benchmark TAES algorithm"""
    ref = generate_events(1000)
    hyp = generate_events(1000)

    result = benchmark(taes_scorer.score, ref, hyp)

    # Assert performance requirements
    assert benchmark.stats["mean"] < 1.0  # Less than 1 second
```

## Documentation Plan

### API Documentation

- OpenAPI/Swagger auto-generated
- Redoc for beautiful API docs
- Postman collection for testing

### Algorithm Documentation

- Mathematical foundations
- Implementation notes
- Validation methodology

### User Guides

- Quick start guide
- Migration from v1.x
- Best practices
- Performance tuning

## Success Metrics

### Technical Metrics

- ✅ 100% algorithmic fidelity (validated)
- ✅ \<100ms latency for single file pair
- ✅ >1000 file pairs/second throughput
- ✅ 99.99% uptime SLA
- ✅ Zero data loss

### Quality Metrics

- ✅ 100% unit test coverage
- ✅ All functions type-hinted
- ✅ Zero security vulnerabilities
- ✅ A+ code quality rating

### Adoption Metrics

- ✅ 10+ research labs using
- ✅ 1000+ API calls/day
- ✅ 5+ citations in papers
- ✅ Active community (>50 stars)

## Timeline Summary

| Phase                  | Duration    | Deliverable                                    | Parity Checkpoint             |
| ---------------------- | ----------- | ---------------------------------------------- | ----------------------------- |
| Foundation             | 5 days      | Alpha pipeline containerized                   | Text parser validated         |
| First Algorithm (TAES) | 5 days      | Beta TAES implementation                       | TAES parity proven            |
| Core Algorithms        | 10 days     | All 5 algorithms in Beta                       | Full algorithm parity         |
| API Layer              | 5 days      | REST API with dual orchestration               | Real-time validation          |
| Production             | 5 days      | Docker/K8s deployment                          | Production metrics            |
| **Total**              | **30 days** | **Production platform with continuous parity** | **100% algorithmic fidelity** |

## Risk Mitigation

### Technical Risks

- **Risk**: Algorithm discrepancies between Alpha and Beta
- **Mitigation**: Continuous dual-pipeline validation with tolerance \< 1e-10

### Adoption Risks

- **Risk**: Users reluctant to trust new implementation
- **Mitigation**: Continuous parity validation proves equivalence

### Performance Risks

- **Risk**: Dual pipeline overhead
- **Mitigation**: Run pipelines in parallel, cache results

## Next Steps

1. **Immediate**: Create GitHub repository with structure
1. **Week 1**: Dockerize Alpha pipeline
1. **Week 2**: Implement basic Beta structure
1. **Week 3**: Begin algorithm reimplementation
1. **Ongoing**: Weekly validation reports

## Conclusion

This dual-pipeline approach ensures we can deliver immediate value while building a modern, scalable platform. The Alpha pipeline provides continuity and trust, while the Beta pipeline delivers performance and features. The comprehensive validation suite guarantees we maintain scientific accuracy throughout the transition.
