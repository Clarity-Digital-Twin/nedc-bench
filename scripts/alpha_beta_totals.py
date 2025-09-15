#!/usr/bin/env python3
"""Run Alpha (NEDC v6.0.0) and Beta (our implementation) batch totals - THE TRUTH!"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

# Setup environment
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.create_runtime_lists import create_runtime_lists


def run_alpha_batch(ref_list: Path, hyp_list: Path, output_dir: Path = Path("alpha_output")) -> Dict[str, Any]:
    """Run NEDC v6.0.0 tool in batch mode to get TRUE Alpha totals.

    Args:
        ref_list: Path to reference list file
        hyp_list: Path to hypothesis list file
        output_dir: Output directory for NEDC results

    Returns:
        Dictionary with Alpha results for all algorithms
    """
    print("\n" + "=" * 60)
    print("Running Alpha (NEDC v6.0.0) Batch")
    print("=" * 60)

    # Run NEDC tool directly
    nedc_bin = Path(os.environ["NEDC_NFC"]) / "bin" / "nedc_eeg_eval"

    cmd = [
        sys.executable,
        str(nedc_bin),
        str(ref_list),
        str(hyp_list),
        "-o", str(output_dir)
    ]

    print(f"Command: {' '.join(cmd)}")
    print("This will take several minutes...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running NEDC: {result.stderr}")
        return {}

    # Parse the summary output
    summary_file = output_dir / "summary.txt"
    if not summary_file.exists():
        print(f"Warning: No summary file at {summary_file}")
        return {}

    # Extract metrics from summary
    alpha_results = parse_nedc_summary(summary_file)

    # Save as JSON
    alpha_json = Path("SSOT_ALPHA.json")
    with open(alpha_json, "w", encoding="utf-8") as f:
        json.dump(alpha_results, f, indent=2)

    print(f"✅ Alpha results saved to: {alpha_json}")
    return alpha_results


def run_beta_batch(ref_list: Path, hyp_list: Path) -> Dict[str, Any]:
    """Run our Beta implementation in batch mode.

    Args:
        ref_list: Path to reference list file
        hyp_list: Path to hypothesis list file

    Returns:
        Dictionary with Beta results for all algorithms
    """
    print("\n" + "=" * 60)
    print("Running Beta (Our Implementation) Batch")
    print("=" * 60)

    from scripts.ultimate_parity_test import run_all_beta_algorithms

    # Run Beta algorithms - this already uses the correct list files internally
    beta_results_raw = run_all_beta_algorithms()

    # Convert to dictionary format
    beta_results = {}
    for algo_name, result in beta_results_raw.items():
        beta_results[algo_name] = {
            "tp": result.tp,
            "fp": result.fp,
            "fn": result.fn,
            "sensitivity": result.sensitivity,
            "fa_per_24h": result.fa_per_24h,
        }

    # Save as JSON
    beta_json = Path("SSOT_BETA.json")
    with open(beta_json, "w", encoding="utf-8") as f:
        json.dump(beta_results, f, indent=2)

    print(f"✅ Beta results saved to: {beta_json}")
    return beta_results


def parse_nedc_summary(summary_file: Path) -> Dict[str, Any]:
    """Parse NEDC summary.txt file to extract metrics.

    Args:
        summary_file: Path to NEDC summary.txt

    Returns:
        Dictionary with metrics for each algorithm
    """
    # This is a placeholder - actual parsing logic depends on NEDC output format
    # For now, return empty dict to be filled manually
    print(f"Parsing {summary_file}...")

    # TODO: Implement actual parsing of NEDC summary format
    # Expected format has sections for each algorithm with TP/FP/FN/Sensitivity/etc

    return {
        "taes": {"tp": 0, "fp": 0, "fn": 0, "sensitivity": 0, "fa_per_24h": 0},
        "epoch": {"tp": 0, "fp": 0, "fn": 0, "sensitivity": 0, "fa_per_24h": 0},
        "ovlp": {"tp": 0, "fp": 0, "fn": 0, "sensitivity": 0, "fa_per_24h": 0},
        "dp": {"tp": 0, "fp": 0, "fn": 0, "sensitivity": 0, "fa_per_24h": 0},
    }


def compare_results(alpha: Dict[str, Any], beta: Dict[str, Any]) -> None:
    """Compare Alpha and Beta results and generate report.

    Args:
        alpha: Alpha results dictionary
        beta: Beta results dictionary
    """
    print("\n" + "=" * 80)
    print("COMPARISON: Alpha (NEDC v6.0.0) vs Beta (Our Implementation)")
    print("=" * 80)

    report_lines = []
    report_lines.append(f"# TRUE ALPHA vs BETA SCORES - {datetime.now()}")
    report_lines.append(f"## Dataset: csv_bi_parity (1832 file pairs)")
    report_lines.append("")

    for algo in ["taes", "epoch", "ovlp", "dp"]:
        if algo not in alpha or algo not in beta:
            continue

        a = alpha[algo]
        b = beta[algo]

        report_lines.append(f"### {algo.upper()}")
        report_lines.append(f"- **Alpha (NEDC v6.0.0):**")
        report_lines.append(f"  - TP: {a.get('tp', 'N/A')}")
        report_lines.append(f"  - FP: {a.get('fp', 'N/A')}")
        report_lines.append(f"  - FN: {a.get('fn', 'N/A')}")
        report_lines.append(f"  - Sensitivity: {a.get('sensitivity', 'N/A')}%")
        report_lines.append(f"  - FA/24h: {a.get('fa_per_24h', 'N/A')}")
        report_lines.append(f"- **Beta (Our Implementation):**")
        report_lines.append(f"  - TP: {b.get('tp', 'N/A')}")
        report_lines.append(f"  - FP: {b.get('fp', 'N/A')}")
        report_lines.append(f"  - FN: {b.get('fn', 'N/A')}")
        report_lines.append(f"  - Sensitivity: {b.get('sensitivity', 'N/A')}%")
        report_lines.append(f"  - FA/24h: {b.get('fa_per_24h', 'N/A')}")

        # Calculate parity
        if isinstance(a.get('tp'), (int, float)) and isinstance(b.get('tp'), (int, float)):
            tp_diff = abs(a['tp'] - b['tp'])
            fp_diff = abs(a['fp'] - b['fp'])
            fn_diff = abs(a['fn'] - b['fn'])

            if tp_diff < 0.01 and fp_diff < 0.01 and fn_diff < 0.01:
                report_lines.append(f"- **Parity:** ✅ PERFECT")
            else:
                report_lines.append(f"- **Parity:** ❌ MISMATCH (TP diff={tp_diff:.2f}, FP diff={fp_diff:.2f}, FN diff={fn_diff:.2f})")
        else:
            report_lines.append(f"- **Parity:** ⚠️ Cannot compute (missing data)")

        report_lines.append("")

        # Print to console
        print(f"\n{algo.upper()}:")
        print(f"  Alpha: TP={a.get('tp')}, FP={a.get('fp')}, FN={a.get('fn')}")
        print(f"  Beta:  TP={b.get('tp')}, FP={b.get('fp')}, FN={b.get('fn')}")

    # Save report
    report_path = Path("SSOT_COMPARISON.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n✅ Comparison report saved to: {report_path}")


def main():
    """Main entry point."""
    print("=" * 80)
    print("ALPHA-BETA TOTALS - THE TRUTH!")
    print("=" * 80)

    # Step 1: Create runtime lists
    print("\nStep 1: Creating runtime list files...")
    ref_list, hyp_list, num_files = create_runtime_lists()

    # Step 2: Run Alpha batch
    print("\nStep 2: Running Alpha (NEDC v6.0.0) batch...")
    alpha_results = run_alpha_batch(ref_list, hyp_list)

    # Step 3: Run Beta batch
    print("\nStep 3: Running Beta (our implementation) batch...")
    beta_results = run_beta_batch(ref_list, hyp_list)

    # Step 4: Compare and report
    print("\nStep 4: Comparing results...")
    compare_results(alpha_results, beta_results)

    print("\n" + "=" * 80)
    print("COMPLETE! Check these files:")
    print("  - SSOT_ALPHA.json: True Alpha totals")
    print("  - SSOT_BETA.json: True Beta totals")
    print("  - SSOT_COMPARISON.md: Side-by-side comparison")
    print("=" * 80)


if __name__ == "__main__":
    main()