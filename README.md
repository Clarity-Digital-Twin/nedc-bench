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

## Data Philosophy

This repository includes:
- ✅ **Test annotations** (`data/csv/`) - Anonymized, synthetic seizure annotations for testing
- ✅ **Expected outputs** (`test/results/`) - Golden outputs for validation
- ✅ **Source code** - Complete NEDC implementation

This repository does NOT include:
- ❌ Real patient data
- ❌ Actual EEG recordings
- ❌ Identifiable information

## Quick Start

```bash
# Install dependencies
pip install numpy scipy lxml toml tomli

# Run the demo
./run_nedc.sh nedc_eeg_eval/v6.0.0/data/lists/ref.list \
              nedc_eeg_eval/v6.0.0/data/lists/hyp.list

# Check output
cat nedc_eeg_eval/v6.0.0/output/summary.txt
```

## License

This project consists of two components with different licensing:

### Original NEDC Software (`nedc_eeg_eval/v6.0.0/`)
- Copyright Temple University Neural Engineering Data Consortium
- No explicit license provided in the original distribution
- Included for research and educational purposes
- Contact Temple University for commercial use inquiries

### NEDC-BENCH Wrapper and Enhancements
- Copyright 2025 Clarity Digital Twin
- Licensed under Apache License 2.0
- See [LICENSE](LICENSE) file for full terms

All new contributions including wrapper scripts, documentation, modernization efforts, and future enhancements are licensed under Apache 2.0. The underlying NEDC algorithms remain the intellectual property of Temple University.