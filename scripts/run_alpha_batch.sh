#!/bin/bash
# Run Alpha (NEDC v6.0.0) batch with proper environment

# Set environment
export NEDC_NFC=$(pwd)/nedc_eeg_eval/v6.0.0
export PYTHONPATH=$NEDC_NFC/lib:$PYTHONPATH

# Create output directory
mkdir -p alpha_output

echo "=========================================="
echo "Running NEDC v6.0.0 (Alpha) Batch"
echo "Time: $(date)"
echo "=========================================="

# Run NEDC tool
python nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval \
    data/csv_bi_parity/csv_bi_export_clean/ref_runtime.list \
    data/csv_bi_parity/csv_bi_export_clean/hyp_runtime.list \
    -o alpha_output 2>&1 | tee alpha_output.log

echo "=========================================="
echo "Alpha run complete!"
echo "Check: alpha_output/summary.txt"
echo "=========================================="