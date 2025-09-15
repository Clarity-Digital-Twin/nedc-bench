# 🧠⚡ NEDC-BENCH — Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Parity](https://img.shields.io/badge/parity-100%25-success.svg)](docs/archive/bugs/FINAL_PARITY_RESULTS.md)

**Production-ready wrapper and reimplementation of Temple University's NEDC EEG Evaluation v6.0.0**

> **⚠️ Independent Project**: This is an open-source contribution, not officially maintained by Temple University, NEDC, or affiliates. We vendor and wrap the original NEDC v6.0.0 software unchanged, and provide a modern reimplementation. All algorithmic credit goes to the original authors (Shah et al., 2021).

## 🎯 What is NEDC-BENCH?

NEDC-BENCH transforms Temple University's NEDC EEG evaluation suite into a production-ready platform. We maintain a **dual-pipeline architecture** that guarantees scoring parity while offering modern infrastructure for scalable deployment.

**The Problem:** NEDC's evaluation software is excellent for research but challenging to deploy — dependency management, I/O conventions, and operational ergonomics make deployment and usage difficult.

**Our Solution:** Best of both worlds — preserve exact scientific behavior while making it effortless to run in production:
- **100% algorithmic parity** with NEDC v6.0.0 (continuously validated)
- **REST API & WebSockets** for programmatic access
- **Docker/Kubernetes ready** with Redis caching and Prometheus metrics
- **92% test coverage** with 187 tests

## 🧱 Architecture — Dual Pipeline Design

```
┌───────────────────────────────────────────────────────────┐
│                    NEDC-BENCH Platform                    │
├───────────────────────────────────────────────────────────┤
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

### Five Scoring Algorithms (All Parity-Validated)
- **TAES** — Time-Aligned Event Scoring
- **DP** — Dynamic Programming Alignment
- **Overlap** — Any-overlap detection
- **Epoch** — 250ms epoch-based sampling
- **IRA** — Inter-Rater Agreement (Cohen's κ)

### When to Use Which Pipeline
- **Alpha (Legacy Wrapper)**: When you need bit-exact reproducibility with NEDC v6.0.0
- **Beta (Modern Rewrite)**: For production deployments requiring speed and modern APIs
- **Dual**: To validate parity between pipelines (used in CI/CD)

## ⚡ Quick Start

### Docker Compose (Recommended)
```bash
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench
docker-compose up -d
curl http://localhost:8000/api/v1/health

# API documentation available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### From Source (Python 3.10+)
```bash
# Using uv (10-100x faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh
make dev  # Installs deps + pre-commit hooks

# Or traditional pip
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api]"

# Verify installation
make test  # Run full test suite
make lint  # Check code quality
```

## 🧰 Usage Examples

### REST API
```python
import requests

# Upload and evaluate EEG annotations
with open("ref.csv_bi", "rb") as ref, open("hyp.csv_bi", "rb") as hyp:
    response = requests.post(
        "http://localhost:8000/api/v1/evaluate",
        files={"reference": ref, "hypothesis": hyp},
        data={"algorithms": ["taes", "epoch", "ira"], "pipeline": "dual"}
    )
    job_id = response.json()["job_id"]

# Get results with parity validation
result = requests.get(f"http://localhost:8000/api/v1/evaluate/{job_id}").json()
print(f"TAES Sensitivity: {result['beta']['taes']['sensitivity']:.2f}%")
print(f"Parity Check: {'✅ PASS' if result['parity']['match'] else '❌ FAIL'}")
```

### WebSocket Real-time Progress
```python
import asyncio
import websockets

async def monitor_job(job_id):
    async with websockets.connect(f"ws://localhost:8000/ws/{job_id}") as ws:
        async for message in ws:
            print(f"Progress: {message}")
```

### Command Line Interface
```bash
# Original NEDC wrapper (preserves exact v6.0.0 behavior)
./run_nedc.sh nedc_eeg_eval/v6.0.0/data/lists/ref.list \
              nedc_eeg_eval/v6.0.0/data/lists/hyp.list

# Python scripts for batch processing
python scripts/run_alpha_complete.py  # Full Alpha pipeline
python scripts/run_beta_batch.py      # All Beta algorithms
python scripts/compare_parity.py      # Compare Alpha vs Beta
```

## 📊 Performance & Validation

### Parity Testing
```bash
# Verify 100% algorithmic match with NEDC v6.0.0
python scripts/compare_parity.py --verbose

# Expected output (exact values):
# ✅ TAES:    TP=133.84, FP=552.77, Sensitivity=12.45%, FA/24h=30.46
# ✅ Epoch:   TP=33704, FP=18816, Sensitivity=11.86%, FA/24h=259.23
# ✅ Overlap: TP=253, FP=536, Sensitivity=23.53%, FA/24h=29.54
# ✅ DP:      TP=328, FP=966, Sensitivity=30.51%, FA/24h=53.23
# ✅ IRA:     Kappa=0.1887 (multi-class Cohen's κ)
```

### Performance Metrics
| Component | Metric | Value | Notes |
|-----------|--------|-------|-------|
| API Latency | P50 | ~250ms | With Redis cache |
| API Latency | P99 | ~2.5s | Cold start |
| Throughput | RPS | ~100 | 4 workers, single node |
| Cache Hit Rate | % | >90% | After warm-up |
| Test Coverage | % | 92% | 187 tests |
| Parity | Match | 100% | All algorithms |

## 🗂️ Project Structure

```
nedc-bench/
├── nedc_bench/           # Modern Beta pipeline (clean-room implementation)
│   ├── algorithms/       # Reimplemented scoring algorithms
│   ├── api/              # FastAPI application & endpoints
│   ├── models/           # Pydantic models for type safety
│   ├── orchestration/    # Dual-pipeline coordinator
│   └── validation/       # Parity checking framework
├── alpha/                # Alpha pipeline wrapper
│   └── wrapper/          # Minimal wrapper around NEDC v6.0.0
├── nedc_eeg_eval/        # Original NEDC v6.0.0 (vendored, unchanged)
│   └── v6.0.0/           # DO NOT MODIFY — reference implementation
├── scripts/              # Utility scripts for testing & validation
│   ├── compare_parity.py # Verify algorithmic equivalence
│   └── ultimate_parity_test.py # Full validation suite
├── tests/                # Comprehensive test suite
├── k8s/                  # Kubernetes manifests
└── docker-compose.yml    # Full stack with Redis & Prometheus
```

## 🔬 Technical Details

### Input Formats
- **CSV_BI**: Temple's annotation format (included examples)
- **XML**: Alternative annotation format
- **List files**: Batch processing of multiple files



### Caching & Performance
- Redis caching provides >10x speedup for repeated evaluations
- Prometheus metrics for production monitoring
- WebSocket support for real-time progress updates
- Async processing for parallel execution

## 📚 Documentation

- 📖 [Installation Guide](docs/installation.md) — Detailed setup instructions
- 🚀 [Quick Start Tutorial](docs/quickstart.md) — Get running in 5 minutes
- 🔬 [Algorithm Details](docs/algorithms/overview.md) — Deep dive into each metric
- 🔌 [API Reference](docs/api/endpoints.md) — Endpoints, examples, OpenAPI access
- 🐳 [Deployment Guide](docs/deployment/overview.md) — Production deployment
- 🔄 [Migration Guide](docs/migration/from-nedc.md) — Moving from vanilla NEDC
- 🐛 [Bug Reports](docs/archive/bugs/) — Fixed issues documentation

## 🔗 Background: TUH EEG Corpus

The Temple University Hospital (TUH) EEG Corpus is the world's largest open EEG dataset. To access:

1. Request access at https://isip.piconepress.com/projects/tuh_eeg/
2. Email completed form to `help@nedcdata.org`
3. Use provided credentials for rsync access

For testing NEDC-BENCH, we include sample data in `nedc_eeg_eval/v6.0.0/data/`.

## Citation

If you use NEDC-BENCH in your research, please cite both:

### Original Algorithms (Temple University)
```bibtex
@incollection{shah2021objective,
  title={Objective Evaluation Metrics for Automatic Classification of EEG Events},
  author={Shah, V. and Golmohammadi, M. and Obeid, I. and Picone, J.},
  booktitle={Signal Processing in Medicine and Biology},
  year={2021},
  publisher={Springer},
  doi={10.1007/978-3-030-36844-9_1}
}
```

### This Platform (NEDC-BENCH)
```bibtex
@software{nedc_bench2025,
  title={NEDC-BENCH: A Modern Dual-Pipeline Platform for EEG Evaluation},
  author={{Clarity Digital Twin}},
  year={2025},
  url={https://github.com/Clarity-Digital-Twin/nedc-bench},
  note={Production wrapper and reimplementation with bug fixes,
        100% parity validation, and modern infrastructure}
}
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/developer/contributing.md) for guidelines.

## License

- **New code** (`nedc_bench/`, `alpha/`, `tests/`): Apache 2.0
- **Original NEDC** (`nedc_eeg_eval/`): No explicit license; © Temple University

## Support

- 🐛 [Issues](https://github.com/Clarity-Digital-Twin/nedc-bench/issues)
- 📚 [Documentation](docs/)
- 🔬 [Original NEDC](https://www.isip.piconepress.com/)

---

*NEDC-BENCH bridges neuroscience research and production systems • Built on Temple University's foundational algorithms*
