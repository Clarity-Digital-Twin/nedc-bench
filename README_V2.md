# 🧠⚡ NEDC-BENCH — Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Parity](https://img.shields.io/badge/parity-100%25-success.svg)](docs/FINAL_PARITY_RESULTS.md)

NEDC-BENCH turns Temple University’s NEDC EEG evaluation suite into a production-ready platform with a dual‑pipeline design that guarantees 100% scoring parity while offering a clean, modern API and CLI.

## 🔗 Quick Links
- Docs: `docs/`
- API (OpenAPI): `http://localhost:8000/docs`
- Parity Results: `docs/FINAL_PARITY_RESULTS.md`
- Issues: https://github.com/Clarity-Digital-Twin/nedc-bench/issues

## ✨ TL;DR
- 100% parity with NEDC v6.0.0 (original code runs under the hood)
- Modern Python API + CLI, Docker/K8s-ready, type-safe models
- Five algorithms: TAES, DP, Overlap, Epoch, IRA — all parity-validated
- 92% test coverage, real-time websockets, Redis-accelerated

## 🧭 Why NEDC-BENCH?
- Scientific accuracy with production ergonomics — no trade-offs
- Unified API over two pipelines:
  - Alpha: wrapper around original NEDC v6.0.0 (unchanged sources)
  - Beta: clean-room reimplementation for modern systems
- Continuous parity validation to eliminate algorithmic drift

## 🧱 Architecture (Dual Pipeline)

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

## 🚀 Features

- Algorithms (parity-validated): TAES, DP Alignment, Overlap, Epoch (250ms), IRA (Cohen’s κ)
- API & runtime: FastAPI, OpenAPI docs, WebSockets for live progress
- Performance: Redis caching (>10x warm-path speedup), parallel execution
- Observability: Prometheus metrics, structured logs
- Deployability: Docker & Kubernetes ready
- Rigor: CSV_BI and XML support; reproducible, type-safe models

## ⚡ Quick Start

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench
docker-compose up -d
curl http://localhost:8000/api/v1/health
# Open API docs
open http://localhost:8000/docs
```

### Option B — From source (Python 3.9+)

```bash
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench

# Fast path with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
make dev  # installs deps

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api]"

# Run tests
make test

# Start API server
uvicorn nedc_bench.api.main:app --reload
```

## 🧰 Usage

### REST API (programmatic)

```python
import requests

with open("reference.csv_bi", "rb") as ref, open("hypothesis.csv_bi", "rb") as hyp:
    r = requests.post(
        "http://localhost:8000/api/v1/evaluate",
        files={"reference": ref, "hypothesis": hyp},
        data={"algorithms": ["taes"], "pipeline": "dual"},
        timeout=60,
    )
    job_id = r.json()["job_id"]

result = requests.get(f"http://localhost:8000/api/v1/evaluate/{job_id}").json()
print(result)
```

### CLI (original and modern)

```bash
# Original NEDC tooling
./run_nedc.sh nedc_eeg_eval/v6.0.0/my_lists/ref.list nedc_eeg_eval/v6.0.0/my_lists/hyp.list

# Modern CLI
nedc-bench evaluate \
  --ref reference.csv_bi \
  --hyp hypothesis.csv_bi \
  --algorithm taes \
  --pipeline dual
```

## 📈 Performance (indicative)

| Metric | Value | Notes |
|--------|-------|-------|
| Cold start latency | ~2.5s | First evaluation |
| Warm cache latency | ~250ms | >10x faster with Redis |
| Throughput | ~100 req/s | 4 workers |
| Test coverage | 92% | 187 tests |
| Parity validation | 100% | All algorithms match |

## 🗂️ Project Structure

```
nedc-bench/
├── nedc_bench/           # Modern Beta pipeline implementation
│   ├── algorithms/       # Clean implementations of 5 algorithms
│   ├── api/              # FastAPI application
│   ├── models/           # Type-safe data models
│   ├── monitoring/       # Metrics and observability
│   ├── orchestration/    # Dual-pipeline orchestrator
│   └── validation/       # Parity checking
├── alpha/                # Alpha pipeline wrapper
│   └── wrapper/          # Python wrapper for original code
├── nedc_eeg_eval/        # Original NEDC v6.0.0 (vendored)
│   └── v6.0.0/           # DO NOT MODIFY — research baseline
├── tests/                # Comprehensive test suite
├── k8s/                  # Kubernetes manifests
├── docs/                 # Documentation
└── docker-compose.yml    # Full stack deployment
```

## ✅ Parity Validation

Run exact-parity checks against NEDC v6.0.0:

```bash
python scripts/compare_parity.py               # all algorithms
python scripts/compare_parity.py --algo epoch  # specific algorithm
python scripts/compare_parity.py --verbose > parity_report.txt
```

Expected (example) — exact match:
- TAES: TP=133.84, FP=552.77, Sensitivity=12.45%
- Epoch: TP=33704, FP=18816, Sensitivity=11.86%
- Overlap: TP=253, FP=536, Sensitivity=23.53%
- DP: TP=328, FP=966, Sensitivity=30.51%
- IRA: Kappa=0.1887

FA/24h is centrally computed in `nedc_bench/utils/metrics.py`:
- Epoch-based: FP scaled by 0.25s epoch duration
- Event-based: FP count directly used
- Values formatted to 4 decimals (NEDC-compatible)

## 🧯 Troubleshooting

### 🚨 NEDC path resolution (common pitfall)
`run_nedc.sh` changes directory to `nedc_eeg_eval/v6.0.0/`, which can cause path issues.

```bash
# CORRECT: List files relative to the NEDC directory
mkdir -p nedc_eeg_eval/v6.0.0/my_lists/
echo '../../data/my_data/ref/file.csv_bi' > nedc_eeg_eval/v6.0.0/my_lists/ref.list
./run_nedc.sh my_lists/ref.list my_lists/hyp.list

# WRONG: Listing from project root will fail
./run_nedc.sh data/ref.list data/hyp.list
```

See `scripts/README.md` for end-to-end examples and `ALPHA_WRAPPER_P0_BUG.md` for details.

## 🔧 Development

```bash
make ci          # lint, typecheck, tests
pytest -q        # run tests
make typecheck   # mypy (strict)
make format      # ruff/format
docker build -f Dockerfile.api -t nedc-bench/api:latest .
```

## 📚 Citation

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

## 📄 License

- New code (`nedc_bench/`, `alpha/`, `tests/`): Apache 2.0
- Original NEDC code (`nedc_eeg_eval/`): no explicit license; © Temple University

## 🤝 Support

- Issues: https://github.com/Clarity-Digital-Twin/nedc-bench/issues
- Docs: `docs/`
- Original NEDC: https://www.isip.piconepress.com/

---

NEDC-BENCH • Bridging neuroscience research and production systems • Built on the foundations of Temple University’s NEDC algorithms
