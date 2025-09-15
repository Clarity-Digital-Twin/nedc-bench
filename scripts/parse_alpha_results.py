#!/usr/bin/env python3
"""Parse Alpha (NEDC v6.0.0) results from summary files."""

import json
from pathlib import Path

def parse_alpha_results():
    """Parse NEDC output to extract totals."""
    nedc_output = Path("nedc_eeg_eval/v6.0.0/output")

    results = {}

    # Parse each algorithm summary

    # 1. TAES - look for SUMMARY section
    taes_file = nedc_output / "summary_taes.txt"
    with open(taes_file) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "SUMMARY:" in line:
            # Next line has totals
            parts = lines[i+1].split()
            results["taes"] = {
                "tp": float(parts[1]),
                "fp": float(parts[2]),
                "fn": float(parts[3])
            }
            break

    # 2. Epoch - look for confusion matrix
    epoch_file = nedc_output / "summary_epoch.txt"
    with open(epoch_file) as f:
        lines = f.readlines()
    for line in lines:
        if "seiz:" in line and "bckg" not in line[:10]:
            parts = line.split()
            # Format: seiz:    33704.00 ( 11.86%)   250459.00 ( 88.14%)
            results["epoch"] = {
                "tp": float(parts[1]),
                "fn": float(parts[4])
            }
        elif "bckg:" in line and "seiz" not in line[:10]:
            parts = line.split()
            # Format: bckg:    18816.00 (  0.31%)  5968398.00 ( 99.69%)
            results["epoch"]["fp"] = float(parts[1])
            break

    # 3. Overlap - look for SUMMARY
    overlap_file = nedc_output / "summary_ovlp.txt"
    with open(overlap_file) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "SUMMARY:" in line:
            parts = lines[i+1].split()
            results["overlap"] = {
                "tp": float(parts[1]),
                "fp": float(parts[2]),
                "fn": float(parts[3])
            }
            break

    # 4. DP Alignment - look for SUMMARY
    dp_file = nedc_output / "summary_dpalign.txt"
    with open(dp_file) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "SUMMARY:" in line:
            parts = lines[i+1].split()
            results["dp"] = {
                "tp": float(parts[1]),
                "fp": float(parts[2]),
                "fn": float(parts[3])
            }
            break

    # Calculate sensitivity and FA/24h
    total_hours = 436.53  # From NEDC output
    for algo, metrics in results.items():
        tp = metrics["tp"]
        fp = metrics["fp"]
        fn = metrics["fn"]

        metrics["sensitivity"] = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
        metrics["fa_per_24h"] = fp * 24 / total_hours

    # Save results
    with open("SSOT_ALPHA.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Alpha Results:")
    for algo, metrics in results.items():
        print(f"\n{algo.upper()}:")
        print(f"  TP: {metrics['tp']:.2f}")
        print(f"  FP: {metrics['fp']:.2f}")
        print(f"  FN: {metrics['fn']:.2f}")
        print(f"  Sensitivity: {metrics['sensitivity']:.2f}%")
        print(f"  FA/24h: {metrics['fa_per_24h']:.2f}")

    return results

if __name__ == "__main__":
    parse_alpha_results()