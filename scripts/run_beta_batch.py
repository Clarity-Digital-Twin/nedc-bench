#!/usr/bin/env python3
"""Run Beta batch - our implementation totals ONLY, no hardcoded bullshit."""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup paths
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ultimate_parity_test import run_all_beta_algorithms


def main():
    """Run Beta algorithms and save SSOT results."""
    print("=" * 60)
    print("Running Beta (Our Implementation) Batch")
    print(f"Time: {datetime.now()}")
    print("=" * 60)

    # Run all Beta algorithms
    print("\nProcessing 1832 file pairs...")
    print("This will take several minutes...")

    beta_results_raw = run_all_beta_algorithms()

    # Convert to clean dictionary format
    beta_results = {}
    for algo_name, result in beta_results_raw.items():
        beta_results[algo_name] = {
            "tp": result.tp,
            "fp": result.fp,
            "fn": result.fn,
            "sensitivity": result.sensitivity,
            "fa_per_24h": result.fa_per_24h,
            "name": result.name
        }

        print(f"\n{algo_name.upper()}:")
        print(f"  TP: {result.tp:.2f}")
        print(f"  FP: {result.fp:.2f}")
        print(f"  FN: {result.fn:.2f}")
        print(f"  Sensitivity: {result.sensitivity:.4f}%")
        print(f"  FA/24h: {result.fa_per_24h:.4f}")

    # Save as JSON
    output_file = Path("SSOT_BETA.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(beta_results, f, indent=2, default=str)

    print(f"\n✅ Beta results saved to: {output_file}")
    print("=" * 60)

    return beta_results


if __name__ == "__main__":
    main()