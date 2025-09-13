# NEDC-BENCH

Modern benchmarking platform for EEG event detection systems, built on top of the NEDC EEG Evaluation tool.

## What's in this Repository

### Core Software (`nedc_eeg_eval/`)
- Original NEDC EEG Evaluation tool v6.0.0
- 5 scoring algorithms for EEG event detection
- Test/demo data (anonymized annotations)
- Expected outputs for validation

### Documentation
- `NEDC_EEG_EVAL_ANALYSIS.md` - Complete technical analysis of the NEDC tool
- `NEDC_BENCH_IMPLEMENTATION_PLAN.md` - Roadmap for modernization

### Scripts
- `run_nedc.sh` - Wrapper script to run the evaluation tool

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