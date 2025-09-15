# NEDC-BENCH User Guide

## What is NEDC-BENCH?
NEDC-BENCH is a modern benchmarking platform for EEG event detection that preserves exact parity with the original NEDC v6.0.0 algorithms and adds a clean API and tooling.

## Key Features
- Dual-pipeline architecture (Alpha = original NEDC, Beta = modern reimplementation)
- Five algorithms: TAES, Epoch, Overlap, DP Alignment, IRA
- REST + WebSocket API with background worker and optional Redis cache
- Thorough tests, parity validation, and developer tooling

## Architecture (at a glance)
- Algorithms: `nedc_bench/algorithms/`
- Orchestration: `nedc_bench/orchestration/dual_pipeline.py`
- API: `nedc_bench/api/` (endpoints, services, middleware)
- Alpha reference: `nedc_eeg_eval/v6.0.0/` (vendored)

## Typical Workflows
- Submit two CSV_BI files to `/api/v1/evaluate` and stream progress over `/ws/{job_id}`.
- Run local scripts for quick checks and parity validation.
- Integrate into CI using the parity script and unit tests.

## Getting Help
- [Installation](../installation.md)
- [Algorithms](../algorithms/overview.md)
- [API](../api/endpoints.md)
- [FAQ](../reference/faq.md)
