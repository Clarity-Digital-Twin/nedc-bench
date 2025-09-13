#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Setup environment for NEDC EEG Evaluation tool
NEDC_NFC="$SCRIPT_DIR/nedc_eeg_eval/v6.0.0"
export NEDC_NFC
export PYTHONPATH="$NEDC_NFC/lib:$PYTHONPATH"

# Change to the NEDC directory
cd "$NEDC_NFC"

# Run the evaluation tool with all arguments
python3 bin/nedc_eeg_eval "$@"