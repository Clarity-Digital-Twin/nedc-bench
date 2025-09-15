#!/usr/bin/env python3
"""Run parity testing between Alpha and Beta pipelines with dynamic path correction."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def create_corrected_lists(original_ref_list, original_hyp_list, data_root):
    """Create corrected list files with proper absolute paths."""
    temp_dir = tempfile.mkdtemp(prefix="nedc_parity_")

    # Read original lists and correct paths
    ref_corrected = Path(temp_dir) / "ref.list"
    hyp_corrected = Path(temp_dir) / "hyp.list"

    # Process reference list
    with open(original_ref_list) as f:
        lines = f.readlines()

    with open(ref_corrected, "w") as f:
        for line in lines:
            if line.strip():
                # Extract just the filename from the original path
                filename = Path(line.strip()).name
                # Create new absolute path
                new_path = Path(data_root) / "ref" / filename
                f.write(f"{new_path.absolute()}\n")

    # Process hypothesis list
    with open(original_hyp_list) as f:
        lines = f.readlines()

    with open(hyp_corrected, "w") as f:
        for line in lines:
            if line.strip():
                filename = Path(line.strip()).name
                new_path = Path(data_root) / "hyp" / filename
                f.write(f"{new_path.absolute()}\n")

    return str(ref_corrected), str(hyp_corrected), temp_dir


def run_alpha_pipeline(ref_list, hyp_list, output_dir):
    """Run the original NEDC tool (Alpha pipeline)."""
    # Set up environment
    nedc_root = Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0"
    env = os.environ.copy()
    env["NEDC_NFC"] = str(nedc_root.absolute())
    env["PYTHONPATH"] = f"{nedc_root}/lib:{env.get('PYTHONPATH', '')}"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Run NEDC tool
    cmd = [
        sys.executable,
        str(nedc_root / "bin" / "nedc_eeg_eval"),
        ref_list,
        hyp_list,
        "--odir",
        output_dir,
    ]

    print("Running Alpha pipeline...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=False, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error running Alpha pipeline:")
        print(result.stderr)
        return False

    print("Alpha pipeline completed successfully")
    return True


def run_beta_pipeline(ref_list, hyp_list, output_dir):
    """Run the modern Beta pipeline."""
    # TODO: Implement Beta pipeline call once it's ready
    print("Beta pipeline not yet implemented")
    return False


def main():
    # Define paths
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    original_ref = data_root / "lists" / "ref.list"
    original_hyp = data_root / "lists" / "hyp.list"

    if not data_root.exists():
        print(f"Error: Data directory not found: {data_root}")
        sys.exit(1)

    # Use timestamp for unique output directory
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = Path(__file__).parent.parent / "output" / f"parity_{timestamp}"

    print("=== NEDC PARITY TEST ===")
    print(f"Data source: {data_root}")
    print(f"Output directory: {output_base}")
    print()

    print("Creating corrected list files...")
    ref_corrected, hyp_corrected, temp_dir = create_corrected_lists(
        original_ref, original_hyp, data_root
    )

    try:
        # Run Alpha pipeline
        alpha_output = str(output_base / "alpha")
        print("\n--- Running Alpha Pipeline (Original NEDC) ---")
        success = run_alpha_pipeline(ref_corrected, hyp_corrected, alpha_output)

        if not success:
            print("Alpha pipeline failed")
            sys.exit(1)

        # Run Beta pipeline (when ready)
        # beta_output = str(output_base / "beta")
        # print(f"\n--- Running Beta Pipeline (Modern Rewrite) ---")
        # run_beta_pipeline(ref_corrected, hyp_corrected, beta_output)

        # TODO: Compare outputs
        print("\n=== PARITY TEST COMPLETE ===")
        print(f"Results saved to: {output_base}")

    finally:
        # Clean up temp files
        import shutil

        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
            print("Cleaned up temporary files")


if __name__ == "__main__":
    main()
