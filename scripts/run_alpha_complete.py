#!/usr/bin/env python3
"""Run complete Alpha (NEDC v6.0.0) batch with correct path handling."""

import os
import subprocess
from pathlib import Path
import json
from datetime import datetime


def create_nedc_list_files():
    """Create list files in NEDC directory with correct relative paths."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Creating NEDC list files...")

    # Base paths
    project_root = Path.cwd()
    nedc_dir = project_root / "nedc_eeg_eval/v6.0.0"
    data_dir = project_root / "data/csv_bi_parity/csv_bi_export_clean"

    # Create lists directory in NEDC
    lists_dir = nedc_dir / "runtime_lists"
    lists_dir.mkdir(exist_ok=True)

    # Get all file pairs
    ref_files = sorted((data_dir / "ref").glob("*.csv_bi"))
    hyp_files = sorted((data_dir / "hyp").glob("*.csv_bi"))

    print(f"Found {len(ref_files)} ref files and {len(hyp_files)} hyp files")

    # Create ref list with paths relative to NEDC directory
    ref_list = lists_dir / "ref_complete.list"
    with open(ref_list, "w") as f:
        for ref_file in ref_files:
            # Path from NEDC dir back to data
            relative_path = f"../../data/csv_bi_parity/csv_bi_export_clean/ref/{ref_file.name}"
            f.write(f"{relative_path}\n")

    # Create hyp list
    hyp_list = lists_dir / "hyp_complete.list"
    with open(hyp_list, "w") as f:
        for hyp_file in hyp_files:
            relative_path = f"../../data/csv_bi_parity/csv_bi_export_clean/hyp/{hyp_file.name}"
            f.write(f"{relative_path}\n")

    print(f"Created lists at: {lists_dir}")
    return "runtime_lists/ref_complete.list", "runtime_lists/hyp_complete.list"


def run_alpha():
    """Run NEDC tool with correct paths."""
    ref_list, hyp_list = create_nedc_list_files()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Alpha NEDC run...")
    print(f"  Ref list: {ref_list}")
    print(f"  Hyp list: {hyp_list}")

    # Run NEDC using wrapper
    cmd = ["./run_nedc.sh", ref_list, hyp_list]
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERROR: NEDC failed with return code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return False

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Alpha NEDC completed successfully!")
    return True


def parse_alpha_results():
    """Parse NEDC output files to extract totals."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Parsing Alpha results...")

    nedc_output = Path("nedc_eeg_eval/v6.0.0/output")

    # Find summary files
    summary_files = {
        "taes": nedc_output / "summary_taes.txt",
        "epoch": nedc_output / "summary_epoch.txt",
        "overlap": nedc_output / "summary_ovlp.txt",
        "dp": nedc_output / "summary_dpalign.txt",
    }

    results = {}

    for algo, summary_file in summary_files.items():
        if not summary_file.exists():
            print(f"WARNING: {summary_file} not found")
            continue

        with open(summary_file) as f:
            lines = f.readlines()

        # Parse totals from last line
        for line in reversed(lines):
            if "TOTAL" in line or line.strip().startswith("Ref:") or "Summary" in line:
                parts = line.split()
                try:
                    # Extract TP, FP, FN (format varies by algorithm)
                    if algo == "taes":
                        # TAES format: different
                        tp = float(parts[2]) if len(parts) > 2 else 0
                        fp = float(parts[3]) if len(parts) > 3 else 0
                        fn = float(parts[4]) if len(parts) > 4 else 0
                    else:
                        # Standard format
                        tp = float(parts[1]) if len(parts) > 1 else 0
                        fp = float(parts[2]) if len(parts) > 2 else 0
                        fn = float(parts[3]) if len(parts) > 3 else 0

                    results[algo] = {
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "sensitivity": tp / (tp + fn) * 100 if (tp + fn) > 0 else 0,
                        "fa_per_24h": fp * 24 / 436.53,  # Total hours in dataset
                    }
                    print(f"  {algo.upper()}: TP={tp}, FP={fp}, FN={fn}")
                    break
                except (IndexError, ValueError) as e:
                    print(f"WARNING: Could not parse {algo} summary: {e}")

    # Save results
    with open("SSOT_ALPHA.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved Alpha results to SSOT_ALPHA.json")
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("ALPHA (NEDC v6.0.0) COMPLETE RUN")
    print("=" * 60)

    if run_alpha():
        parse_alpha_results()
        print("\n✅ Alpha run complete! Check SSOT_ALPHA.json for results.")
    else:
        print("\n❌ Alpha run failed!")
