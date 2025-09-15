#!/usr/bin/env python3
"""RUN TRUE PARITY TEST - NO HARDCODED BULLSHIT!

This uses our DualPipelineOrchestrator to run BOTH:
- Alpha: Actual NEDC v6.0.0 tool
- Beta: Our implementation

On the SAME data with NO hardcoded values!
"""

import os
import sys
from pathlib import Path

# Set up NEDC environment
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


def main():
    """Run true parity test using DualPipelineOrchestrator"""
    print("=" * 80)
    print("🚀 TRUE PARITY TEST - NO HARDCODED VALUES!")
    print("=" * 80)
    print()

    # Use our corrected list files pointing to actual data
    data_dir = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    ref_list = data_dir / "ref_correct.list"
    hyp_list = data_dir / "hyp_correct.list"

    if not ref_list.exists() or not hyp_list.exists():
        print("❌ ERROR: Corrected list files not found!")
        print("Run: python scripts/create_correct_lists.py")
        return 1

    print(f"Using ref list: {ref_list}")
    print(f"Using hyp list: {hyp_list}")
    print()

    # Initialize orchestrator (runs BOTH pipelines)
    orchestrator = DualPipelineOrchestrator(tolerance=1e-10)

    # Test each algorithm
    algorithms = ["taes", "epoch", "ovlp", "dp"]

    all_results = {}

    for algo in algorithms:
        print(f"\n{'=' * 60}")
        print(f"Running {algo.upper()} on 1832 file pairs...")
        print(f"{'=' * 60}")

        try:
            # This runs BOTH Alpha (NEDC v6.0.0) and Beta (our code)
            # and compares them automatically!
            result = orchestrator.evaluate_lists(
                ref_list=str(ref_list),
                hyp_list=str(hyp_list),
                algorithm=algo
            )

            all_results[algo] = result

            # Print summary
            print(f"\n{algo.upper()} Results:")
            print(f"  Total files processed: {result.get('total_files', 0)}")
            print(f"  Parity passed: {'✅ YES' if result.get('parity_passed') else '❌ NO'}")

            if 'summary' in result:
                summary = result['summary']
                print(f"\n  Alpha (NEDC v6.0.0):")
                print(f"    TP: {summary.get('alpha_tp', 'N/A')}")
                print(f"    FP: {summary.get('alpha_fp', 'N/A')}")
                print(f"    FN: {summary.get('alpha_fn', 'N/A')}")

                print(f"\n  Beta (Our Implementation):")
                print(f"    TP: {summary.get('beta_tp', 'N/A')}")
                print(f"    FP: {summary.get('beta_fp', 'N/A')}")
                print(f"    FN: {summary.get('beta_fn', 'N/A')}")

                print(f"\n  Differences:")
                print(f"    TP diff: {summary.get('tp_diff', 'N/A')}")
                print(f"    FP diff: {summary.get('fp_diff', 'N/A')}")
                print(f"    FN diff: {summary.get('fn_diff', 'N/A')}")

        except Exception as e:
            print(f"  ❌ Error running {algo}: {e}")
            all_results[algo] = {"error": str(e)}

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY - TRUE PARITY TEST")
    print("=" * 80)

    all_passed = True
    for algo in algorithms:
        if algo in all_results:
            passed = all_results[algo].get('parity_passed', False)
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {algo.upper():10s}: {status}")
            if not passed:
                all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL ALGORITHMS HAVE PERFECT PARITY!")
        print("Alpha (NEDC v6.0.0) = Beta (Our Implementation)")
    else:
        print("⚠️ Some algorithms need adjustment")
        print("This is the TRUE comparison, no hardcoded values!")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())