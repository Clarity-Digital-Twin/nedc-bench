#!/usr/bin/env python3
"""Create correct list files for NEDC v6.0.0 tool pointing to our actual data location."""

from pathlib import Path


def create_correct_lists():
    """Create ref.list and hyp.list pointing to actual CSV files in our data directory."""
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

    # Get all CSV_BI files
    ref_dir = data_root / "ref"
    hyp_dir = data_root / "hyp"

    ref_files = sorted(ref_dir.glob("*.csv_bi"))
    hyp_files = sorted(hyp_dir.glob("*.csv_bi"))

    print(f"Found {len(ref_files)} ref files and {len(hyp_files)} hyp files")

    # Create corrected list files with absolute paths
    ref_list_path = data_root / "ref_correct.list"
    hyp_list_path = data_root / "hyp_correct.list"

    with open(ref_list_path, "w", encoding="utf-8") as f:
        f.writelines(f"{ref_file.absolute()}\n" for ref_file in ref_files)

    with open(hyp_list_path, "w", encoding="utf-8") as f:
        f.writelines(f"{hyp_file.absolute()}\n" for hyp_file in hyp_files)

    print(f"Created: {ref_list_path}")
    print(f"Created: {hyp_list_path}")

    # Also create lists in the lists/ subdirectory for compatibility
    lists_dir = data_root / "lists"

    ref_list_alt = lists_dir / "ref_correct.list"
    hyp_list_alt = lists_dir / "hyp_correct.list"

    with open(ref_list_alt, "w", encoding="utf-8") as f:
        f.writelines(f"{ref_file.absolute()}\n" for ref_file in ref_files)

    with open(hyp_list_alt, "w", encoding="utf-8") as f:
        f.writelines(f"{hyp_file.absolute()}\n" for hyp_file in hyp_files)

    print(f"Also created: {ref_list_alt}")
    print(f"Also created: {hyp_list_alt}")

    return ref_list_path, hyp_list_path


if __name__ == "__main__":
    ref_list, hyp_list = create_correct_lists()
    print("\nReady to run NEDC v6.0.0 with:")
    print(f"  ./run_nedc.sh {ref_list} {hyp_list}")
