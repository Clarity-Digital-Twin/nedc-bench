# NEDC-BENCH: Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## What is NEDC-BENCH?

NEDC-BENCH is a **dual-pipeline benchmarking platform** that modernizes the Temple University Neural Engineering Data Consortium's EEG evaluation tool (v6.0.0) while maintaining 100% algorithmic fidelity. It provides researchers and developers with both the trusted original algorithms and a modern, production-ready API for evaluating EEG event detection systems, particularly focused on seizure detection.

### Why Dual Pipelines?

The dual-pipeline architecture serves a critical purpose in computational neuroscience research:

1. **Scientific Reproducibility**: The Alpha pipeline preserves the exact algorithms from published research (Shah et al., 2021), ensuring results can be replicated and validated against existing literature.

2. **Modern Infrastructure**: The Beta pipeline provides the same algorithms in a cloud-native, type-safe, production-ready implementation that can scale and integrate with modern ML/AI systems.

3. **Continuous Validation**: Every evaluation can be run through both pipelines simultaneously, with automatic parity checking to ensure the modern implementation maintains perfect algorithmic fidelity.

4. **Migration Path**: Organizations can gradually transition from legacy systems to modern infrastructure while maintaining confidence in their results.

## Architecture

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
│  │ • Research-grade      │    │ • Type-safe Python    │      │
│  │ • Text-based I/O     │    │ • Async/parallel      │      │
│  │ • 100% fidelity       │    │ • Cloud-native        │      │
│  └──────────────────────┘    └──────────────────────┘      │
│             ↓                           ↓                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Unified API & Result Validator          │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 🎯 Five Scoring Algorithms
All algorithms maintain exact parity with NEDC v6.0.0:

- **DP Alignment**: Dynamic programming-based event alignment with configurable penalties
- **Epoch-based**: Fixed 250ms window frame-based scoring
- **Overlap**: Temporal overlap measurement with guard width
- **TAES**: Time-Aligned Event Scoring with FA/24hr metrics
- **IRA**: Inter-Rater Agreement using Cohen's kappa

### 🚀 Production-Ready Infrastructure

- **FastAPI REST API** with OpenAPI documentation
- **WebSocket support** for real-time progress tracking
- **Redis caching** with >10x performance improvement on warm paths
- **Prometheus metrics** for observability
- **Docker & Kubernetes** deployment ready
- **Rate limiting** and error handling
- **92% test coverage** with 187 tests

### 🔬 Scientific Rigor

- **100% algorithmic fidelity** to published research
- **Continuous parity validation** between pipelines
- **Support for CSV_BI and XML** annotation formats
- **Comprehensive metrics** matching academic standards

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench

# Start the platform
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# View API documentation
open http://localhost:8000/docs
```

### Local Development

```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
make dev

# Run tests
make test

# Start API server
uvicorn nedc_bench.api.main:app --reload
```

## Usage Examples

### REST API Evaluation

```python
import requests

# Submit evaluation job
with open("reference.csv_bi", "rb") as ref, open("hypothesis.csv_bi", "rb") as hyp:
    response = requests.post(
        "http://localhost:8000/api/v1/evaluate",
        files={"reference": ref, "hypothesis": hyp},
        data={"algorithms": ["taes"], "pipeline": "dual"}
    )
    job_id = response.json()["job_id"]

# Get results
result = requests.get(f"http://localhost:8000/api/v1/evaluate/{job_id}")
print(result.json())
```

### Command Line (Original NEDC Tool)

```bash
# Run original NEDC evaluation
./run_nedc.sh data/lists/ref.list data/lists/hyp.list

# Or use the modern CLI
nedc-bench evaluate --ref reference.csv_bi --hyp hypothesis.csv_bi --algorithm taes
```

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Cold start latency | ~2.5s | First evaluation |
| Warm cache latency | ~250ms | >10x faster with Redis |
| Throughput | ~100 req/s | With 4 workers |
| Test coverage | 92% | 187 tests |
| Parity validation | 100% | All algorithms match |

## Project Structure

```
nedc-bench/
├── nedc_bench/           # Modern Beta pipeline implementation
│   ├── algorithms/       # Clean implementations of 5 algorithms
│   ├── api/             # FastAPI application
│   ├── models/          # Type-safe data models
│   ├── monitoring/      # Metrics and observability
│   ├── orchestration/   # Dual-pipeline orchestrator
│   └── validation/      # Parity checking
├── alpha/               # Alpha pipeline wrapper
│   └── wrapper/         # Python wrapper for original code
├── nedc_eeg_eval/       # Original NEDC v6.0.0 (vendored)
│   └── v6.0.0/         # DO NOT MODIFY - research baseline
├── tests/              # Comprehensive test suite
├── k8s/                # Kubernetes manifests
├── docs/               # Documentation
└── docker-compose.yml  # Full stack deployment
```

## For Researchers

This platform ensures your EEG scoring maintains perfect compatibility with published research while gaining modern capabilities:

- **Reproducible Results**: Alpha pipeline guarantees exact match with Shah et al. (2021)
- **Batch Processing**: Evaluate thousands of files in parallel
- **Real-time Monitoring**: WebSocket progress tracking
- **Export Formats**: JSON, CSV, or original text format

## For Dr. Picone and NEDC Team

This implementation:
1. **Preserves** the exact algorithms from your published work
2. **Modernizes** the infrastructure for cloud deployment
3. **Validates** every result against the original implementation
4. **Enables** integration with modern ML pipelines
5. **Maintains** scientific rigor while adding production capabilities

## Development

```bash
# Run all quality checks
make ci

# Run specific algorithm tests
pytest tests/algorithms/test_taes.py -v

# Check type safety
make typecheck

# Format code
make format

# Build Docker image
docker build -f Dockerfile.api -t nedc-bench/api:latest .
```

## Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Citation

If you use NEDC-BENCH in your research, please cite:

```bibtex
@incollection{shah2021objective,
  title={Objective Evaluation Metrics for Automatic Classification of EEG Events},
  author={Shah, V. and Golmohammadi, M. and Obeid, I. and Picone, J.},
  booktitle={Signal Processing in Medicine and Biology},
  pages={1--26},
  year={2021},
  publisher={Springer}
}
```

## License

- **New code** (nedc_bench/, alpha/, tests/): Apache 2.0
- **Original NEDC code** (nedc_eeg_eval/): No explicit license, copyright Temple University

## Support

- **Issues**: [GitHub Issues](https://github.com/Clarity-Digital-Twin/nedc-bench/issues)
- **Documentation**: [Full Docs](docs/)
- **Original NEDC**: [ISIP Website](https://www.isip.piconepress.com/)

---

Built with dedication to advancing EEG research through modern, reliable software engineering.