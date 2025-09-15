#!/usr/bin/env python3
"""CRITICAL PARITY TEST - Alpha vs Beta pipeline comparison"""

import sys
from pathlib import Path

# Add nedc_bench to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


def main():
    print("=" * 80)
    print("CRITICAL PARITY TEST - ALPHA vs BETA")
    print("=" * 80)

    # Set up paths
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    if not data_root.exists():
        print(f"ERROR: Data not found at {data_root}")
        sys.exit(1)

    print(f"Data source: {data_root}")
    print(f"Reference files: {ref_list}")
    print(f"Hypothesis files: {hyp_list}")
    print()

    # Create orchestrator
    orchestrator = DualPipelineOrchestrator()

    # Run TAES comparison first (simplest algorithm)
    print("Testing TAES algorithm parity...")
    print("-" * 40)

    try:
        result = orchestrator.run_taes_comparison(str(ref_list), str(hyp_list))

        print(f"\nAlpha execution time: {result.execution_time_alpha:.2f}s")
        print(f"Beta execution time: {result.execution_time_beta:.2f}s")
        print(f"Speedup: {result.speedup:.2f}x")
        print()

        print("PARITY VALIDATION REPORT:")
        print(f"Status: {'✅ PASSED' if result.parity_passed else '❌ FAILED'}")

        if not result.parity_passed:
            print("\n⚠️  CRITICAL: PARITY MISMATCH DETECTED!")
            print("Differences found:")
            for diff in result.parity_report.differences:
                print(f"  - {diff}")
        else:
            print("\n🎉 SUCCESS: Perfect parity achieved!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("=" * 80)

    if not result.parity_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
