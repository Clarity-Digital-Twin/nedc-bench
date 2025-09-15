#!/usr/bin/env python3
"""Direct parity test between Alpha and Beta pipelines"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Set environment
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_alpha_on_files(ref_list, hyp_list):
    """Run Alpha pipeline directly"""
    print("Running Alpha pipeline...")

    # Create temp output dir
    output_dir = tempfile.mkdtemp(prefix="alpha_output_")

    cmd = [
        sys.executable,
        f"{os.environ['NEDC_NFC']}/bin/nedc_eeg_eval",
        ref_list,
        hyp_list,
        "--odir",
        output_dir,
    ]

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Alpha failed: {result.stderr}")
        return None

    # Read TAES results
    taes_file = Path(output_dir) / "summary_taes.txt"
    if taes_file.exists():
        with open(taes_file) as f:
            content = f.read()
            # Extract key metrics
            lines = content.strip().split("\n")
            for line in lines[-20:]:  # Check last 20 lines for summary
                if "sens:" in line.lower() or "sensitivity" in line.lower():
                    print(f"Alpha TAES: {line.strip()}")

    return output_dir


def run_beta_on_files(ref_list, hyp_list):
    """Run Beta pipeline"""
    print("Running Beta pipeline...")

    try:
        from nedc_bench.algorithms.taes import TAESScorer
        from nedc_bench.models.annotations import AnnotationFile

        # Read file lists
        with open(ref_list) as f:
            ref_files = [line.strip() for line in f if line.strip()]
        with open(hyp_list) as f:
            hyp_files = [line.strip() for line in f if line.strip()]

        if len(ref_files) != len(hyp_files):
            print(f"ERROR: Mismatched file counts: {len(ref_files)} ref vs {len(hyp_files)} hyp")
            return None

        print(f"Processing {len(ref_files)} file pairs...")

        # Run TAES on first file as test
        scorer = TAESScorer()
        ref_ann = AnnotationFile.from_csv_bi(Path(ref_files[0]))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_files[0]))

        result = scorer.evaluate(ref_ann.events, hyp_ann.events)

        print(f"Beta TAES (first file): TP={result.tp}, FP={result.fp}, FN={result.fn}")
        print(f"Beta metrics: Sensitivity={result.sensitivity:.4f}, FA/24h={result.fa_per_24h:.2f}")

        return result

    except Exception as e:
        print(f"Beta failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("DIRECT PARITY TEST - CRITICAL VALIDATION")
    print("=" * 80)

    # Set up paths
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    # Create corrected lists
    print("Creating corrected file lists...")
    temp_dir = tempfile.mkdtemp(prefix="parity_lists_")

    # Fix paths in lists
    ref_corrected = Path(temp_dir) / "ref.list"
    hyp_corrected = Path(temp_dir) / "hyp.list"

    with open(ref_list) as f:
        lines = f.readlines()
    with open(ref_corrected, "w") as f:
        for line in lines:
            if line.strip():
                filename = Path(line.strip()).name
                new_path = data_root / "ref" / filename
                f.write(f"{new_path.absolute()}\n")

    with open(hyp_list) as f:
        lines = f.readlines()
    with open(hyp_corrected, "w") as f:
        for line in lines:
            if line.strip():
                filename = Path(line.strip()).name
                new_path = data_root / "hyp" / filename
                f.write(f"{new_path.absolute()}\n")

    print(f"Lists created in {temp_dir}")
    print()

    # Run both pipelines
    alpha_output = run_alpha_on_files(str(ref_corrected), str(hyp_corrected))
    print()
    beta_result = run_beta_on_files(str(ref_corrected), str(hyp_corrected))

    print()
    print("=" * 80)

    if alpha_output and beta_result:
        print("✅ Both pipelines executed successfully")
        print(f"Alpha output: {alpha_output}")
        print("TODO: Full comparison logic needed")
    else:
        print("❌ FAILED: One or both pipelines failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
