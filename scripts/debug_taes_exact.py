#!/usr/bin/env python3
"""Debug TAES exact values to find the source of difference."""

import json
import os
import sys
from pathlib import Path

# Set up environment
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.utils.params import load_nedc_params, map_event_label


def get_exact_alpha_values():
    """Get exact Alpha values from the ultimate test hardcoded values."""
    return {
        "tp": 133.84137545872733,
        "fp": 552.7689020231412,
        "fn": 941.1586245412731,
        "sensitivity": 12.450360507788584,
        "fa_per_24h": 30.461710971183077,
    }


def calculate_beta_values():
    """Calculate Beta values from scratch."""
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

    # Read file lists
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with ref_list.open(encoding="utf-8") as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with hyp_list.open(encoding="utf-8") as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    # Fix paths
    ref_files = [str(data_root / "ref" / Path(f).name) for f in ref_files]
    hyp_files = [str(data_root / "hyp" / Path(f).name) for f in hyp_files]

    print(f"Processing {len(ref_files)} file pairs...")

    # Initialize scorer and params
    params = load_nedc_params()
    scorer = TAESScorer(target_label="seiz")

    total_tp = 0.0
    total_fp = 0.0
    total_fn = 0.0
    total_duration = 0.0

    # Process each file
    for i, (ref_file, hyp_file) in enumerate(zip(ref_files, hyp_files)):
        ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))

        # Normalize labels
        for ev in ref_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)
        for ev in hyp_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)

        # Score
        result = scorer.score(ref_ann.events, hyp_ann.events)

        total_tp += result.true_positives
        total_fp += result.false_positives
        total_fn += result.false_negatives
        total_duration += ref_ann.duration

        # Debug first file differences
        if i == 0:
            print(f"\nFirst file: {Path(ref_file).name}")
            print(f"  TP: {result.true_positives}")
            print(f"  FP: {result.false_positives}")
            print(f"  FN: {result.false_negatives}")

    # Calculate metrics
    sensitivity = (total_tp / (total_tp + total_fn) * 100) if (total_tp + total_fn) > 0 else 0
    fa_per_24h = (total_fp / total_duration) * 86400 if total_duration > 0 else 0

    return {
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "sensitivity": sensitivity,
        "fa_per_24h": fa_per_24h,
        "duration": total_duration,
    }


def main():
    print("=" * 80)
    print("TAES EXACT VALUE COMPARISON")
    print("=" * 80)

    # Get values
    alpha = get_exact_alpha_values()
    beta = calculate_beta_values()

    # Compare with full precision
    print("\nAlpha (NEDC v6.0.0):")
    print(f"  TP: {alpha['tp']:.20f}")
    print(f"  FP: {alpha['fp']:.20f}")
    print(f"  FN: {alpha['fn']:.20f}")
    print(f"  Sensitivity: {alpha['sensitivity']:.20f}%")
    print(f"  FA/24h: {alpha['fa_per_24h']:.20f}")

    print("\nBeta (Our Implementation):")
    print(f"  TP: {beta['tp']:.20f}")
    print(f"  FP: {beta['fp']:.20f}")
    print(f"  FN: {beta['fn']:.20f}")
    print(f"  Sensitivity: {beta['sensitivity']:.20f}%")
    print(f"  FA/24h: {beta['fa_per_24h']:.20f}")
    print(f"  Duration: {beta['duration']:.2f} seconds")

    print("\nExact Differences:")
    print(f"  TP diff: {beta['tp'] - alpha['tp']:.20f}")
    print(f"  FP diff: {beta['fp'] - alpha['fp']:.20f}")
    print(f"  FN diff: {beta['fn'] - alpha['fn']:.20f}")
    print(f"  Sensitivity diff: {beta['sensitivity'] - alpha['sensitivity']:.20f}%")
    print(f"  FA/24h diff: {beta['fa_per_24h'] - alpha['fa_per_24h']:.20f}")

    # Check if differences are exactly zero
    tp_exact = beta['tp'] == alpha['tp']
    fp_exact = beta['fp'] == alpha['fp']
    fn_exact = beta['fn'] == alpha['fn']

    print("\nExact Match Status:")
    print(f"  TP exact match: {tp_exact}")
    print(f"  FP exact match: {fp_exact}")
    print(f"  FN exact match: {fn_exact}")

    if not all([tp_exact, fp_exact, fn_exact]):
        print("\n⚠️ DIFFERENCES DETECTED - INVESTIGATING...")
        print("Next step: Check individual file processing for discrepancies")


if __name__ == "__main__":
    main()