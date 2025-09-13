#!/bin/bash
#
# file: $NEDC_NFC/src/nedc_eeg_eval_demo/nedc_eeg_eval_demo.sh
#
# revision history:
#
# 20250721 (DH): initial version
#
#==============================================================================
#
# setup and run scoring algorithm on experiment
#
#==============================================================================

# set ROOT_DIR variable
#
ROOT_DIR=$(realpath "$(dirname "$0")/..")
export ROOT_DIR

# necessary paths
#
OUTPUT_DIR="$ROOT_DIR/test/output"
RESULTS_DIR="$ROOT_DIR/test/results"
LIST_DIR="$ROOT_DIR/data/lists"
LIB_DIR="$ROOT_DIR/lib"
TOOL_DIR="$ROOT_DIR/src"
DOCS_DIR="$ROOT_DIR/docs"

# create the final nedc_eeg_eval output directories
#
mkdir -p $OUTPUT_DIR
mkdir -p $RESULTS_DIR

# set ref and hyp list variables
#
HYP_LIST="$LIST_DIR/hyp.list"
REF_LIST="$LIST_DIR/ref.list"

# set the parameter file
#
PARAM="$DOCS_DIR/params/nedc_eeg_eval_params_v00.toml"

# set the command line arguments
#
CMD_ARG="-p $PARAM -o $OUTPUT_DIR $REF_LIST $HYP_LIST"

# set the python script
#
DRIVER_SCRIPT="$TOOL_DIR/nedc_eeg_eval/nedc_eeg_eval.py"

# set the final command
#
CMD="python $DRIVER_SCRIPT $CMD_ARG"

# run scoring on the train dataset
#
echo "==== Scoring the Dataset ===="
echo "Scoring the Train Dataset Started on: $(date "+%D %T")"
$CMD
echo "Scoring the Train Dataset Finished on: $(date "+%D %T")"

echo "==== Verifying output vs results ===="

# lines to ignore (timestamps / run metadata)
#
IGNORE_PATTERNS=(
  '^[[:space:]]*=\+$'
  '^[[:space:]]*Date:'
  '^[[:space:]]*File:'                            
  '^[[:space:]]*Version:'
  '^[[:space:]]*Mod Time:'
  '^[[:space:]]*NEDC EEG Eval Successfully Completed'
  '^[[:space:]]*[^:]*:[[:space:]]*/.*$'           
  '^[[:space:]]*/.*$'                            
)

# build args for diff
#
DIFF_IGNORE_ARGS=()
for pat in "${IGNORE_PATTERNS[@]}"; do
  DIFF_IGNORE_ARGS+=(-I "$pat")
done

# quiet check first
#
if diff -qr "${DIFF_IGNORE_ARGS[@]}" "$RESULTS_DIR" "$OUTPUT_DIR" > /dev/null; then
  echo "No differences between $OUTPUT_DIR and $RESULTS_DIR"
else
  echo "Differences found between $OUTPUT_DIR and $RESULTS_DIR:"

  # show full diff but keep the same ignore rules
  #
  diff -ruN "${DIFF_IGNORE_ARGS[@]}" "$RESULTS_DIR" "$OUTPUT_DIR"
  exit 1
fi

 echo "==== Verification finished ===="
#
# end of file
