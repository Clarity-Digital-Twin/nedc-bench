# 🧠⚡ NEDC-BENCH — Modern EEG Benchmarking Platform

[![Tests](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml/badge.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench/actions/workflows/api.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](https://github.com/Clarity-Digital-Twin/nedc-bench)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Parity](https://img.shields.io/badge/parity-100%25-success.svg)](docs/archive/bugs/FINAL_PARITY_RESULTS.md)

NEDC-BENCH turns Temple University’s NEDC EEG evaluation suite into a production-ready platform with a dual‑pipeline design that guarantees 100% scoring parity while offering a clean, modern API and CLI.

## 🔗 Quick Links
- Docs: `docs/`
- API (OpenAPI): `http://localhost:8000/docs`
- Parity Results: `docs/archive/bugs/FINAL_PARITY_RESULTS.md`
- Issues: https://github.com/Clarity-Digital-Twin/nedc-bench/issues

## ✨ TL;DR
- 100% parity with NEDC v6.0.0 (original code runs under the hood)
- Modern Python API + CLI, Docker/K8s-ready, type-safe models
- Five algorithms: TAES, DP, Overlap, Epoch, IRA — all parity-validated
- 92% test coverage, real-time websockets, Redis-accelerated

## 👤 Who Is This For?
- Researchers, ML engineers, and platform teams working with TUH/NEDC EEG.
- Anyone who needs rigorous, NEDC‑exact scoring inside automated pipelines.
- Teams deploying reproducible EEG evaluation services in cloud or on‑prem.

## 🧩 Background: TUH/NEDC EEG Resources
- TUH/NEDC curate the world’s largest open EEG research corpora and tooling.
- Home: https://isip.piconepress.com/projects/nedc/html/tuh_eeg/
- Corpora (examples): TUEG, TUAB, TUAR, TUEP, TUEV, TUSZ, TUSL.
- Software (examples): EVAL (scoring), EEGR/ERDR (ResNet decoders), EAS (annotation), PYED (EDF I/O).
- Documentation hubs: Electrodes (ELEC), Annotations (ANNO), Reports (RPRT).

## 🔑 Access: How to Get TUH EEG
- Request access by completing the TUH EEG form and emailing it to `help@nedcdata.org` with subject “Download The TUH EEG Corpus”.
- Once approved, you’ll receive credentials to browse or rsync datasets.
- Browse: `https://www.isip.piconepress.com/projects/nedc/data/`
- Quick rsync test:
  - `rsync -auxvL nedc-tuh-eeg@www.isip.piconepress.com:data/tuh_eeg/TEST .`
- Download a specific corpus/release (replace `AAAA` and `vx.x.x`):
  - `rsync -auxvL nedc-tuh-eeg@www.isip.piconepress.com:data/tuh_eeg/AAAA/vx.x.x/ .`
- Tip: Include `-L` to follow links; Windows users can use MobaXterm for rsync.

## 📦 About NEDC Eval v6.0.0 (Upstream)
- NEDC announced v6.0.0 of their EEG scoring software and provide a tarball distribution:
  - https://isip.piconepress.com/projects/nedc/data/tuh_eeg/tuh_eeg_software/nedc_eeg_eval_v6.0.0.tar.gz
- It is excellent, research-grade software designed for scientific rigor and reproducibility within their environment.
- Practical challenge: outside the lab, hosting, dependency pinning, I/O conventions, and ops ergonomics can make large-scale, automated, or cloud deployments hard.

## 💡 Why This Project Exists (in plain terms)
We wanted the best of both worlds: preserve the exact scientific behavior of NEDC’s scoring while making it effortless to run, automate, and integrate in modern systems.

- Reproducibility-by-default: containerized, pinned dependencies, parity tests on every PR.
- Maintainability: a thin wrapper that runs the original v6.0.0 code unchanged, plus a clean-room modern reimplementation.
- Automation & agents: API-first design enables programmatic workflows, CI/CD, and AI agents to drive evaluations reliably.
- Operability: first-class logging, metrics, caching, and scaling for production workloads.
- Portability: simple Docker/Compose/K8s paths; also easy local `uv/pip` installs.
- Interop: typed Python models, REST/WebSocket APIs, and a CLI usable in any pipeline.
- Scientific safety: 100% parity with v6.0.0 validated continuously to prevent drift.

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
# Open API docs: visit http://localhost:8000/docs
# (macOS: `open`; Linux: `xdg-open`; Windows: `start`)
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

with open("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaovk_s001_t000.csv_bi", "rb") as ref, \
     open("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaovk_s001_t000.csv_bi", "rb") as hyp:
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

# Modern CLI (when installed as a package)
# If the `nedc-bench` command is unavailable, use the API example above.
nedc-bench evaluate \
  --ref nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaovk_s001_t000.csv_bi \
  --hyp nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaovk_s001_t000.csv_bi \
  --algorithm taes \
  --pipeline dual
```

### What You Need (Prereqs)
- Python 3.9+ (for from‑source installs) or Docker.
- OS: Linux or macOS; Windows via WSL2 recommended.
- Optional: Redis for caching; Prometheus for metrics.

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

### When To Use Alpha vs Beta
- Alpha (legacy wrapper): audits, bit‑exact reproducibility, authoritative baseline.
- Beta (modern rewrite): speed, integration ergonomics, type safety, cloud runtime.
- Dual: run both and validate equivalence (used in CI and parity testing).

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

What 100% parity means here:
- Same inputs produce the same outputs as NEDC v6.0.0 for all five algorithms.
- We match file formats (CSV_BI/XML), rounding/precision, and aggregation rules.
- Differences are treated as bugs and blocked by tests until resolved.

Related docs:
- Quickstart: `docs/quickstart.md`
- Data formats: `docs/migration/data-formats.md`
- From NEDC to NEDC‑BENCH: `docs/migration/from-nedc.md`
- API docs: `docs/api/openapi.md`
- Glossary: `docs/reference/glossary.md`

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

## ❓ FAQ
- Why not just use NEDC Eval v6 directly?
  - You can. We even ship it and run it unchanged (Alpha pipeline). NEDC‑BENCH adds an API/CLI, containers, caching, metrics, and CI parity checks so you can operate it at scale reliably.
- Is the original NEDC source modified?
  - No. We vendor v6.0.0 as-is and call it via a thin wrapper.
- Can I use only the modern pipeline?
  - Yes. Use `--pipeline beta` to run the clean-room implementation. Parity tests keep it aligned.
- Do I need TUH credentials to try this?
  - For your own corpora access, yes. For local parity demos, we include small example lists and `csv_bi` samples under `nedc_eeg_eval/v6.0.0/data/`.
- How should I cite?
  - Cite NEDC-BENCH and the NEDC foundational work (see Citation below).

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

Note: NEDC‑BENCH is not affiliated with Temple University or NEDC. Names are used to reference upstream resources and algorithms; all credit to the original authors.

## 🤝 Support

- Issues: https://github.com/Clarity-Digital-Twin/nedc-bench/issues
- Docs: `docs/`
- Original NEDC: https://www.isip.piconepress.com/

---

NEDC-BENCH • Bridging neuroscience research and production systems • Built on the foundations of Temple University’s NEDC algorithms
