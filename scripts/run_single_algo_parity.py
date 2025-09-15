#!/usr/bin/env python3
"""Run parity test for a SINGLE algorithm - manageable and trackable."""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Set up NEDC environment
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


def main():
    """Run parity test for single algorithm specified as argument."""
    if len(sys.argv) != 2:
        print("Usage: python run_single_algo_parity.py <algorithm>")
        print("Algorithms: taes, epoch, ovlp, dp")
        return 1

    algo = sys.argv[1].lower()
    if algo not in ["taes", "epoch", "ovlp", "dp"]:
        print(f"Invalid algorithm: {algo}")
        return 1

    print(f"{'=' * 60}")
    print(f"Running {algo.upper()} Parity Test")
    print(f"Time: {datetime.now()}")
    print(f"{'=' * 60}")

    # Use corrected list files
    data_dir = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    ref_list = data_dir / "ref_correct.list"
    hyp_list = data_dir / "hyp_correct.list"

    if not ref_list.exists() or not hyp_list.exists():
        print("ERROR: Run create_correct_lists.py first!")
        return 1

    # Count files
    with open(ref_list, encoding="utf-8") as f:
        num_files = len([l for l in f if l.strip()])
    print(f"Processing {num_files} file pairs...")

    # Run just this algorithm
    orchestrator = DualPipelineOrchestrator(tolerance=1e-10)

    print(f"\nRunning {algo.upper()}...")
    print("This may take several minutes...")

    result = orchestrator.evaluate_lists(
        ref_list=str(ref_list),
        hyp_list=str(hyp_list),
        algorithm=algo
    )

    # Save results to file
    output_file = Path(f"TRUE_SCORES_{algo.upper()}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    # Print summary
    print(f"\n{algo.upper()} SUMMARY:")
    print(f"  Files processed: {result.get('total_files', 0)}")
    print(f"  Parity: {'✅ PASS' if result.get('parity_passed') else '❌ FAIL'}")

    if 'summary' in result:
        s = result['summary']
        print(f"\nAlpha (NEDC v6.0.0): TP={s.get('alpha_tp')}, FP={s.get('alpha_fp')}, FN={s.get('alpha_fn')}")
        print(f"Beta (Our Code):     TP={s.get('beta_tp')}, FP={s.get('beta_fp')}, FN={s.get('beta_fn')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())