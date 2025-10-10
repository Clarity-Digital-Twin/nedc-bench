# SzCORE Analysis and Insights for NEDC-BENCH

## Overview

SzCORE (https://epilepsybenchmarks.com) is an open seizure detection benchmarking platform that provides automated evaluation of containerized algorithms on high-quality EEG datasets. This analysis examines their architecture and identifies opportunities for NEDC-BENCH.

## Key Architecture Components

### 1. Algorithm Submission Model

- **YAML-based metadata**: Each algorithm described via structured YAML (title, authors, version, Docker image, license)
- **JSON Schema validation**: Strict schema enforcement for algorithm definitions
- **Docker containerization**: All algorithms packaged as Docker images with standardized I/O
- **Public registry requirement**: Images must be publicly accessible (Docker Hub, GHCR, etc.)

### 2. CI/CD Pipeline

- **PR-based submission**: Contributors submit via GitHub PRs adding YAML files
- **Automated validation**:
  - YAML schema validation using jsonschema-cli
  - Docker image pull verification
  - Output format validation (TSV with specific headers)
- **GitHub Actions execution**: Algorithms run on GitHub's infrastructure
- **Static website generation**: Hugo + TailwindCSS for results display

### 3. Evaluation Framework

- **Standardized metrics**:
  - Sample-based: sensitivity, precision, F1, false positive rate
  - Event-based: same metrics but at event level
- **Multiple datasets**: CHB-MIT, DianaLund, SeizeIT, Siena, TUH
- **JSON results storage**: Metrics stored as JSON per algorithm/dataset pair
- **Statistical reporting**: Mean and standard deviation across recordings

### 4. Infrastructure Design

- **Minimal test data**: Small EDF files (25KB) for CI validation
- **Volume mounting**: `/data` for input, `/output` for results
- **Environment variables**: `INPUT` and `OUTPUT` specify file paths
- **Non-privileged execution**: Containers run as restricted user

## Identified Issues and Improvements

### Current Problems in SzCORE

1. **No versioning for results**: Results overwrite without history tracking
1. **Limited error handling**: CI fails hard on any validation error
1. **No local testing support**: Contributors can't easily test before PR
1. **Hardcoded dataset list**: Adding new datasets requires code changes
1. **No partial evaluation**: Can't run on subset of datasets
1. **Missing algorithm comparison**: No direct A/B comparison tools
1. **No reproducibility guarantees**: No seed control or determinism checks

### Potential Enhancements for NEDC-BENCH

1. **Dual-pipeline validation**:

   - Run both NEDC original and modern implementation
   - Automated equivalence checking between pipelines
   - Differential testing for algorithm changes

1. **Enhanced metadata**:

   - Add computational requirements (CPU, memory, runtime)
   - Include training data specifications
   - Document preprocessing requirements
   - Specify EEG channel configurations

1. **Local development tools**:

   ```bash
   make test-algorithm ALGO=my-algorithm.yaml
   make validate-output OUTPUT=results.tsv
   make compare-algorithms ALGO1=gotman ALGO2=modern
   ```

1. **Versioned benchmarking**:

   - Git-tracked result history
   - Performance regression detection
   - Temporal analysis of algorithm improvements

1. **Extended metrics**:

   - Latency measurements
   - Memory consumption
   - Computational complexity analysis
   - Channel-specific performance

1. **Dataset management**:

   - Dynamic dataset discovery
   - Configurable evaluation subsets
   - Cross-validation support
   - Private dataset capability

## Integration Opportunities for NEDC-BENCH

### 1. Adopt Container Strategy

```dockerfile
# NEDC-BENCH algorithm template
FROM python:3.11-slim
WORKDIR /app

# Install NEDC dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy algorithm implementation
COPY nedc_bench/ ./nedc_bench/

# Standardized entry point
ENV NEDC_NFC=/app
ENV PYTHONPATH=/app/lib
CMD ["python", "-m", "nedc_bench.evaluate", \
     "--ref", "/data/ref.list", \
     "--hyp", "/data/hyp.list", \
     "--output", "/output/scores.txt"]
```

### 2. Implement PR-based Benchmarking

```yaml
# .github/workflows/benchmark.yml
name: NEDC Benchmark
on:
  pull_request:
    paths:
      - 'algorithms/**'
      - 'nedc_bench/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run NEDC evaluation
        run: |
          make docker-build
          make docker-test
      - name: Compare with baseline
        run: |
          make compare-baseline
```

### 3. Create Comparison Framework

```python
# nedc_bench/comparison.py
class AlgorithmComparator:
    def compare_scores(self, alpha_results, beta_results):
        """Compare NEDC original vs modern implementation"""
        return {
            "dp_alignment": self._compare_metric("dp", alpha_results, beta_results),
            "epoch_based": self._compare_metric("epoch", alpha_results, beta_results),
            "overlap": self._compare_metric("overlap", alpha_results, beta_results),
            "taes": self._compare_metric("taes", alpha_results, beta_results),
            "ira": self._compare_metric("ira", alpha_results, beta_results),
        }
```

### 4. Build Result Dashboard

- Adapt SzCORE's Hugo template for NEDC metrics
- Display algorithm comparison tables
- Show performance trends over time
- Include computational cost analysis

## Recommendations for NEDC-BENCH

### Phase 1: Container Infrastructure (Week 1-2)

1. Create Dockerfile for NEDC wrapper
1. Implement standardized I/O interface
1. Add Docker Compose for local testing
1. Document container usage

### Phase 2: CI/CD Pipeline (Week 3-4)

1. Setup GitHub Actions workflows
1. Implement automated testing on PRs
1. Add result archiving
1. Create performance regression checks

### Phase 3: Comparison Framework (Week 5-6)

1. Build dual-pipeline orchestrator
1. Implement numerical equivalence checking
1. Add differential testing tools
1. Create visualization utilities

### Phase 4: Web Dashboard (Week 7-8)

1. Adapt SzCORE's website structure
1. Customize for NEDC metrics
1. Add interactive comparisons
1. Deploy to GitHub Pages

## Conclusion

SzCORE provides a solid architectural pattern for benchmarking EEG algorithms. Their containerization approach, automated CI/CD, and web-based results display offer excellent templates for NEDC-BENCH. However, there are clear opportunities for enhancement, particularly around versioning, local testing, and algorithm comparison.

The key insight is that NEDC-BENCH can leverage SzCORE's infrastructure patterns while adding unique value through:

1. Dual-pipeline validation (original vs modern)
1. Comprehensive algorithmic equivalence testing
1. Enhanced computational metrics
1. Better developer experience with local testing tools

This positions NEDC-BENCH as both a benchmarking platform AND a migration tool for modernizing legacy EEG analysis code.
\\n\[Archived\] Reference analysis; core implementation finalized in docs/.
