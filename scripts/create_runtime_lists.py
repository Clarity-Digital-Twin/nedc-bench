#!/usr/bin/env python3
"""Create runtime list files - NO HARDCODING!"""

import sys
from pathlib import Path


def create_runtime_lists(data_dir=None):
    """Create list files at runtime from actual CSV_BI files.

    Args:
        data_dir: Optional data directory path. If None, uses default location.

    Returns:
        Tuple of (ref_list_path, hyp_list_path, num_files)
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    else:
        data_dir = Path(data_dir)

    ref_dir = data_dir / "ref"
    hyp_dir = data_dir / "hyp"

    # Get all CSV_BI files - sorted for consistency
    ref_files = sorted(ref_dir.glob("*.csv_bi"))
    hyp_files = sorted(hyp_dir.glob("*.csv_bi"))

    if not ref_files:
        raise FileNotFoundError(f"No CSV_BI files found in {ref_dir}")
    if not hyp_files:
        raise FileNotFoundError(f"No CSV_BI files found in {hyp_dir}")

    if len(ref_files) != len(hyp_files):
        raise ValueError(f"Mismatch: {len(ref_files)} ref vs {len(hyp_files)} hyp files")

    # Verify matching basenames
    ref_basenames = {f.name for f in ref_files}
    hyp_basenames = {f.name for f in hyp_files}
    if ref_basenames != hyp_basenames:
        missing_in_hyp = ref_basenames - hyp_basenames
        missing_in_ref = hyp_basenames - ref_basenames
        raise ValueError(
            f"File mismatch!\nMissing in hyp: {missing_in_hyp}\nMissing in ref: {missing_in_ref}"
        )

    # Create list files with absolute paths
    ref_list = data_dir / "ref_runtime.list"
    hyp_list = data_dir / "hyp_runtime.list"

    with open(ref_list, "w", encoding="utf-8") as f:
        f.writelines(f"{ref_file.absolute()}\n" for ref_file in ref_files)

    with open(hyp_list, "w", encoding="utf-8") as f:
        f.writelines(f"{hyp_file.absolute()}\n" for hyp_file in hyp_files)

    print("Created runtime lists:")
    print(f"  {ref_list}")
    print(f"  {hyp_list}")
    print(f"  Files: {len(ref_files)} pairs")

    return ref_list, hyp_list, len(ref_files)


if __name__ == "__main__":
    try:
        ref_list, hyp_list, num_files = create_runtime_lists()
        print(f"\n✅ Success! Ready to run with {num_files} file pairs")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
