#!/usr/bin/env python3
"""Create file lists for NEDC processing.

This utility creates properly formatted list files for batch processing
with correct relative paths for the NEDC tool.
"""

import argparse
from pathlib import Path


def create_lists(data_dir: Path, output_dir: Path, prefix: str = ""):
    """Create ref.list and hyp.list files with correct paths.

    Args:
        data_dir: Directory containing ref/ and hyp/ subdirectories
        output_dir: Where to write the list files
        prefix: Optional prefix for paths in list files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all CSV_BI files
    ref_files = sorted((data_dir / "ref").glob("*.csv_bi"))
    hyp_files = sorted((data_dir / "hyp").glob("*.csv_bi"))

    if len(ref_files) != len(hyp_files):
        print(f"WARNING: Mismatch - {len(ref_files)} ref files, {len(hyp_files)} hyp files")

    # Write ref.list
    ref_list = output_dir / "ref.list"
    with ref_list.open("w") as f:
        for ref_file in ref_files:
            if prefix:
                f.write(f"{prefix}/ref/{ref_file.name}\n")
            else:
                f.write(f"{ref_file}\n")

    # Write hyp.list
    hyp_list = output_dir / "hyp.list"
    with hyp_list.open("w") as f:
        for hyp_file in hyp_files:
            if prefix:
                f.write(f"{prefix}/hyp/{hyp_file.name}\n")
            else:
                f.write(f"{hyp_file}\n")

    print(f"Created {ref_list} with {len(ref_files)} files")
    print(f"Created {hyp_list} with {len(hyp_files)} files")

    return ref_list, hyp_list


def main():
    parser = argparse.ArgumentParser(description="Create file lists for NEDC processing")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/csv_bi_parity/csv_bi_export_clean"),
        help="Directory containing ref/ and hyp/ subdirectories",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/csv_bi_parity/csv_bi_export_clean/lists"),
        help="Where to write the list files",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix for paths in list files (e.g., '../../data/csv_bi_parity/csv_bi_export_clean')",
    )
    parser.add_argument(
        "--subset",
        type=int,
        help="Create lists with only first N files (for testing)",
    )

    args = parser.parse_args()

    if args.subset:
        # Create subset for testing
        subset_dir = args.output_dir / f"subset_{args.subset}"
        create_lists(args.data_dir, subset_dir, args.prefix)
        print(f"Created subset lists with first {args.subset} files")
    else:
        create_lists(args.data_dir, args.output_dir, args.prefix)


if __name__ == "__main__":
    main()
