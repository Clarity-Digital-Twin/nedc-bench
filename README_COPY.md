# 🧠⚡ NEDC-BENCH — Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Parity](https://img.shields.io/badge/parity-100%25-success.svg)](docs/archive/bugs/FINAL_PARITY_RESULTS.md)

**Production-ready wrapper and reimplementation of Temple University's NEDC EEG Evaluation v6.0.0**

> **Note**: This is an independent open-source project, not officially maintained by Temple University, NEDC, or their affiliates. We vendor and wrap the original NEDC v6.0.0 software unchanged while providing a modern reimplementation. All algorithmic credit goes to the original authors (Shah et al., 2021).

## What is NEDC-BENCH?

A dual-pipeline platform that makes NEDC's EEG evaluation algorithms production-ready while guaranteeing 100% scoring parity. Run the original research code or our modern reimplementation — both produce identical results.

**Key Features:**
- ✅ **100% algorithmic parity** with NEDC v6.0.0 (continuously validated)
- 🚀 **REST API & WebSockets** for programmatic access
- 🐳 **Docker/Kubernetes ready** with Redis caching and Prometheus metrics
- 🧪 **92% test coverage** with 187 tests
- 🔧 **Critical bug fixes** for boundary conditions and duration calculations

## Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench
docker-compose up -d
# API docs at http://localhost:8000/docs
```

### Python (3.9+)
```bash
# Using uv (fast)
curl -LsSf https://astral.sh/uv/install.sh | sh
make dev

# Or pip
pip install -e ".[api]"
uvicorn nedc_bench.api.main:app --reload
```

### Test Parity
```bash
python scripts/compare_parity.py  # Verify 100% match with NEDC v6.0.0
```

## Architecture

```
NEDC-BENCH Platform
├── Alpha Pipeline (Original)     │  Beta Pipeline (Modern)
│   • NEDC v6.0.0 unchanged       │  • Clean-room rewrite
│   • Research-grade accuracy     │  • Type-safe Python
│   • Text-based I/O              │  • Async/parallel
└──────────────────────────────────────────────────────────
              Unified API with Parity Validation
```

**Five Algorithms:** TAES, DP Alignment, Overlap, Epoch (250ms), IRA (Cohen's κ)

## Usage

### REST API
```python
import requests

# Upload and evaluate
with open("ref.csv_bi", "rb") as ref, open("hyp.csv_bi", "rb") as hyp:
    r = requests.post("http://localhost:8000/api/v1/evaluate",
                      files={"reference": ref, "hypothesis": hyp},
                      data={"algorithms": ["taes"], "pipeline": "dual"})
    job_id = r.json()["job_id"]

# Get results
result = requests.get(f"http://localhost:8000/api/v1/evaluate/{job_id}").json()
```

### Command Line
```bash
# Original NEDC wrapper
./run_nedc.sh ref.list hyp.list

# Modern CLI (when installed)
nedc-bench evaluate --ref ref.csv_bi --hyp hyp.csv_bi --algorithm taes
```

## Documentation

- 📖 [Installation Guide](docs/installation.md)
- 🚀 [Quick Start Tutorial](docs/quickstart.md)
- 🔬 [Algorithm Details](docs/algorithms/)
- 🔌 [API Reference](docs/api/)
- 🐳 [Deployment Guide](docs/deployment/)
- 🔄 [Migration from NEDC](docs/migration/from-nedc.md)

## Why NEDC-BENCH?

**Problem:** NEDC's evaluation software is excellent for research but challenging to deploy at scale.

**Solution:** We provide:
- **Reproducibility**: Containerized with pinned dependencies
- **Reliability**: Extensive testing and continuous parity validation
- **Performance**: Redis caching, parallel execution, WebSocket progress
- **Ergonomics**: Modern API, type safety, structured logging
- **Safety**: Original code runs unchanged; parity guaranteed

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

### This Platform
```bibtex
@software{nedc_bench2025,
  title={NEDC-BENCH: A Modern Dual-Pipeline Platform for EEG Evaluation},
  author={{Clarity Digital Twin}},
  year={2025},
  url={https://github.com/Clarity-Digital-Twin/nedc-bench},
  note={Production wrapper and reimplementation with bug fixes and 100% parity}
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/developer/contributing.md).

## License

- **New code** (`nedc_bench/`, `alpha/`, `tests/`): Apache 2.0
- **Original NEDC** (`nedc_eeg_eval/`): No explicit license; © Temple University

## Support

- 🐛 [Issues](https://github.com/Clarity-Digital-Twin/nedc-bench/issues)
- 📚 [Documentation](docs/)
- 🔬 [Original NEDC](https://www.isip.piconepress.com/)

---

*NEDC-BENCH bridges neuroscience research and production systems • Built on Temple University's foundational algorithms*