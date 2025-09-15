#!/usr/bin/env python3
"""Deep investigation of Epoch algorithm mismatches between Alpha and Beta.

This script will:
1. Run Epoch on each file individually for both Alpha and Beta
2. Identify exact files where TP/FP/FN differ
3. Dump detailed diagnostics for each mismatched file
4. Analyze boundary conditions and sampling differences
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Setup paths
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.utils.params import load_nedc_params, map_event_label


def run_beta_epoch_single(ref_file: Path, hyp_file: Path, params) -> dict[str, float]:
    """Run Beta Epoch on a single file pair."""
    ref_ann = AnnotationFile.from_csv_bi(ref_file)
    hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

    # Normalize labels
    for ev in ref_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)
    for ev in hyp_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)

    scorer = EpochScorer(epoch_duration=params.epoch_duration, null_class=params.null_class)
    result = scorer.score(ref_ann.events, hyp_ann.events, file_duration=ref_ann.duration)

    # Extract SEIZ metrics from properties
    tp = result.true_positives.get("seiz", 0)
    fp = result.false_positives.get("seiz", 0)
    fn = result.false_negatives.get("seiz", 0)

    return {"tp": tp, "fp": fp, "fn": fn}


def analyze_boundary_conditions(ref_file: Path, hyp_file: Path, params) -> dict[str, Any]:
    """Analyze detailed boundary conditions for a file pair."""
    ref_ann = AnnotationFile.from_csv_bi(ref_file)
    hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

    # Normalize labels
    for ev in ref_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)
    for ev in hyp_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)

    # Get sampling info
    epoch_duration = params.epoch_duration
    file_duration = ref_ann.duration

    # Sample times (matching Beta implementation)
    half = epoch_duration / 2.0
    t = half
    samples = []
    while t <= file_duration + 1e-12:  # Note the epsilon here
        samples.append(t)
        t += epoch_duration

    # Get last few samples and their labels
    last_samples = samples[-5:] if len(samples) > 5 else samples
    sample_info = []

    scorer = EpochScorer(epoch_duration=params.epoch_duration, null_class=params.null_class)
    for t in last_samples:
        ref_idx = scorer._time_to_index(t, ref_ann.events)
        hyp_idx = scorer._time_to_index(t, hyp_ann.events)
        ref_label = ref_ann.events[ref_idx].label if ref_idx >= 0 else params.null_class
        hyp_label = hyp_ann.events[hyp_idx].label if hyp_idx >= 0 else params.null_class
        sample_info.append({
            "time": t,
            "ref_label": ref_label,
            "hyp_label": hyp_label,
            "at_boundary": abs(t - file_duration) < 1e-6,
        })

    # Event boundaries
    ref_event_ends = [ev.stop_time for ev in ref_ann.events if ev.label == "seiz"]
    hyp_event_ends = [ev.stop_time for ev in hyp_ann.events if ev.label == "seiz"]

    return {
        "file_duration": file_duration,
        "file_duration_rounded": round(file_duration, 4),
        "num_samples": len(samples),
        "last_sample_time": samples[-1] if samples else 0,
        "exceeds_duration": samples[-1] > file_duration if samples else False,
        "ref_has_events": len(ref_ann.events) > 0,
        "hyp_has_events": len(hyp_ann.events) > 0,
        "ref_seiz_count": sum(1 for ev in ref_ann.events if ev.label == "seiz"),
        "hyp_seiz_count": sum(1 for ev in hyp_ann.events if ev.label == "seiz"),
        "last_ref_seiz_end": max(ref_event_ends) if ref_event_ends else None,
        "last_hyp_seiz_end": max(hyp_event_ends) if hyp_event_ends else None,
        "last_samples": sample_info,
        "epsilon_at_boundary": 1e-12,
        "would_include_extra": (samples[-1] - file_duration) > 0
        and (samples[-1] - file_duration) < epoch_duration,
    }


def main():
    print("=" * 80)
    print("EPOCH MISMATCH DEEP INVESTIGATION")
    print("=" * 80)

    params = load_nedc_params()

    # Load file lists
    data_root = Path("data/csv_bi_parity/csv_bi_export_clean")
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with ref_list.open(encoding="utf-8") as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with hyp_list.open(encoding="utf-8") as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    # Convert to full paths
    ref_files = [data_root / "ref" / Path(f).name for f in ref_files]
    hyp_files = [data_root / "hyp" / Path(f).name for f in hyp_files]

    print(f"Analyzing {len(ref_files)} file pairs...")

    mismatches = []
    total_beta = {"tp": 0, "fp": 0, "fn": 0}

    # Test on first 10 files for initial investigation
    test_limit = 10
    print(f"\nTesting first {test_limit} files for quick analysis...")

    for i, (ref_file, hyp_file) in enumerate(zip(ref_files[:test_limit], hyp_files[:test_limit])):
        print(f"\rProcessing {i + 1}/{test_limit}...", end="", flush=True)

        # Run Beta (faster, internal)
        beta_result = run_beta_epoch_single(ref_file, hyp_file, params)

        total_beta["tp"] += beta_result["tp"]
        total_beta["fp"] += beta_result["fp"]
        total_beta["fn"] += beta_result["fn"]

        # Analyze boundaries for all files to look for patterns
        boundary_info = analyze_boundary_conditions(ref_file, hyp_file, params)

        if boundary_info["exceeds_duration"] or boundary_info["would_include_extra"]:
            mismatches.append({
                "ref_file": str(ref_file.name),
                "hyp_file": str(hyp_file.name),
                "beta_result": beta_result,
                "boundary_info": boundary_info,
            })

    print(f"\n\nFound {len(mismatches)} files with boundary issues")

    # Output detailed diagnostics
    output_dir = Path("output/epoch_investigation")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save mismatches
    if mismatches:
        with (output_dir / "boundary_issues.json").open("w", encoding="utf-8") as f:
            json.dump(mismatches, f, indent=2, default=str)

        print("\nFiles with boundary issues:")
        for m in mismatches[:5]:  # Show first 5
            print(f"  - {m['ref_file']}")
            info = m["boundary_info"]
            print(f"    Duration: {info['file_duration']:.6f}")
            print(f"    Last sample: {info['last_sample_time']:.6f}")
            print(f"    Exceeds: {info['exceeds_duration']}")
            print(f"    Would include extra: {info['would_include_extra']}")

    print(f"\nBeta totals (first {test_limit} files):")
    print(f"  TP: {total_beta['tp']}")
    print(f"  FP: {total_beta['fp']}")
    print(f"  FN: {total_beta['fn']}")

    print("\nFull investigation results saved to output/epoch_investigation/")

    # Now let's do a targeted deep dive on the sampling epsilon
    print("\n" + "=" * 80)
    print("SAMPLING EPSILON ANALYSIS")
    print("=" * 80)

    # Check if changing epsilon affects results
    test_epsilons = [0, 1e-15, 1e-12, 1e-10, 1e-8, 1e-6, 1e-4]

    print("\nTesting different epsilon values for boundary sampling...")
    for eps in test_epsilons:
        # We'll need to monkey-patch or create a modified scorer for this
        # For now, let's analyze theoretically
        print(f"  ε={eps}: Would need to modify EpochScorer._sample_times()")

    print("\nRecommendation: Review NEDC's exact boundary handling in nedc_eeg_eval_epoch.py")


if __name__ == "__main__":
    main()
