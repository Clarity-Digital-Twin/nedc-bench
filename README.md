# NEDC-BENCH: Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## What is NEDC-BENCH?

NEDC-BENCH transforms Temple University's Neural Engineering Data Consortium EEG evaluation algorithms into a **production-ready benchmarking platform**. By implementing a dual-pipeline architecture, we deliver both the trusted original algorithms and a modern cloud-native API while maintaining 100% algorithmic fidelity for evaluating seizure detection systems.

### The Problem We Solved

Research-grade EEG evaluation tools face a critical challenge: they must maintain perfect scientific accuracy while meeting modern production requirements. The original NEDC tool delivers trusted algorithms but lacks the infrastructure needed for cloud deployment, API integration, and real-time processing.

### Our Solution: Dual-Pipeline Architecture

1. **Alpha Pipeline**: Wraps the original NEDC v6.0.0 code, preserving exact algorithmic behavior from published research
2. **Beta Pipeline**: Clean-room reimplementation with modern software engineering practices
3. **Continuous Validation**: Every result validated across both pipelines to guarantee parity
4. **Unified API**: Single interface for accessing both implementations with automatic verification

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    NEDC-BENCH Platform                    │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────────────┐    ┌───────────────────────┐   │
│  │   Pipeline Alpha      │    │   Pipeline Beta       │   │
│  │  (Legacy Wrapper)     │    │  (Modern Rewrite)     │   │
│  ├───────────────────────┤    ├───────────────────────┤   │
│  │ • Original NEDC code  │    │ • Clean architecture  │   │
│  │ • Research-grade      │    │ • Type-safe Python    │   │
│  │ • Text-based I/O      │    │ • Async/parallel      │   │
│  │ • 100% fidelity       │    │ • Cloud-native        │   │
│  └───────────────────────┘    └───────────────────────┘   │
│             ↓                           ↓                 │
│  ┌──────────────────────────────────────────────────┐     │
│  │           Unified API & Result Validator         │     │
│  └──────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
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

## Key Benefits

### 🧬 Scientific Integrity
- **Bit-perfect accuracy**: Every calculation matches the original NEDC v6.0.0 implementation
- **Reproducible research**: Results align with Shah et al. (2021) publication
- **Continuous validation**: Dual-pipeline architecture ensures zero algorithmic drift
- **Academic standards**: Comprehensive metrics for peer-reviewed research

### ⚡ Modern Performance
- **10x faster**: Redis caching accelerates repeated evaluations
- **Parallel processing**: Batch evaluate thousands of files simultaneously
- **Real-time monitoring**: WebSocket streaming for live progress updates
- **Cloud scale**: Kubernetes-ready for distributed computing

### 🛡️ Production Reliability
- **92% test coverage**: 187 comprehensive tests ensure stability
- **Type safety**: Full MyPy strict type checking prevents runtime errors
- **Observability**: Prometheus metrics and structured logging
- **Fault tolerance**: Graceful degradation and automatic retries

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

## Known Issues & Troubleshooting

### 🚨 NEDC Path Resolution (Common Source of Errors)

The `run_nedc.sh` script **changes directory** to `nedc_eeg_eval/v6.0.0/` before running, causing path confusion:

**Problem:** "File not found" errors even when files exist

**Solution:**
```bash
# CORRECT: List files in NEDC directory structure
mkdir -p nedc_eeg_eval/v6.0.0/my_lists/
echo '../../data/my_data/ref/file.csv_bi' > nedc_eeg_eval/v6.0.0/my_lists/ref.list
./run_nedc.sh my_lists/ref.list my_lists/hyp.list

# WRONG: List files in project root
./run_nedc.sh data/ref.list data/hyp.list  # Will fail!
```

See `scripts/README.md` for detailed examples and `ALPHA_WRAPPER_P0_BUG.md` for investigation details.

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

**NEDC-BENCH** • Bridging neuroscience research and production systems • Built on the foundations of Temple University's NEDC algorithms