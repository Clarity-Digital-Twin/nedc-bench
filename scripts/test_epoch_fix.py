#!/usr/bin/env python3
"""Test that Epoch algorithm fix works"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import AnnotationFile

def test_single_file():
    """Test Epoch on a single file to verify fix"""
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

    # Get first file
    ref_file = data_root / "ref" / "aaaaaajy_s001_t000.csv_bi"
    hyp_file = data_root / "hyp" / "aaaaaajy_s001_t000.csv_bi"

    if not ref_file.exists():
        print(f"Test file not found: {ref_file}")
        return False

    print(f"Testing Epoch fix on: {ref_file.name}")
    print("-" * 50)

    # Load annotations
    ref_ann = AnnotationFile.from_csv_bi(ref_file)
    hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

    print(f"Reference events: {len(ref_ann.events)}")
    print(f"Hypothesis events: {len(hyp_ann.events)}")
    print(f"File duration: {ref_ann.duration} seconds")

    # Create scorer
    scorer = EpochScorer(epoch_duration=1.0)

    # Score
    result = scorer.score(ref_ann.events, hyp_ann.events, ref_ann.duration)

    print("\nConfusion Matrix:")
    for ref_label in result.confusion_matrix:
        for hyp_label in result.confusion_matrix[ref_label]:
            count = result.confusion_matrix[ref_label][hyp_label]
            if count > 0:
                print(f"  {ref_label} -> {hyp_label}: {count}")

    # Test new properties
    print("\nTesting new properties:")
    print(f"Has true_positives? {hasattr(result, 'true_positives')}")
    print(f"Has false_positives? {hasattr(result, 'false_positives')}")
    print(f"Has false_negatives? {hasattr(result, 'false_negatives')}")

    if hasattr(result, 'true_positives'):
        tp = result.true_positives
        fp = result.false_positives
        fn = result.false_negatives

        print(f"\nTrue Positives: {tp}")
        print(f"False Positives: {fp}")
        print(f"False Negatives: {fn}")

        # Check if seiz exists
        if "seiz" in tp:
            print(f"\nFor 'seiz' label:")
            print(f"  TP: {tp['seiz']}")
            print(f"  FP: {fp['seiz']}")
            print(f"  FN: {fn['seiz']}")

            # Calculate sensitivity
            if tp['seiz'] + fn['seiz'] > 0:
                sensitivity = tp['seiz'] / (tp['seiz'] + fn['seiz']) * 100
                print(f"  Sensitivity: {sensitivity:.4f}%")

        return True
    else:
        print("\n❌ Properties not found!")
        return False

def test_multiple_files():
    """Test on multiple files to accumulate results"""
    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

    ref_dir = data_root / "ref"
    hyp_dir = data_root / "hyp"

    files = list(ref_dir.glob("*.csv_bi"))[:10]  # Test first 10

    print(f"\nTesting {len(files)} files...")
    print("-" * 50)

    scorer = EpochScorer(epoch_duration=1.0)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for ref_file in files:
        hyp_file = hyp_dir / ref_file.name

        if not hyp_file.exists():
            continue

        try:
            ref_ann = AnnotationFile.from_csv_bi(ref_file)
            hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

            result = scorer.score(ref_ann.events, hyp_ann.events, ref_ann.duration)

            if "seiz" in result.true_positives:
                total_tp += result.true_positives["seiz"]
                total_fp += result.false_positives["seiz"]
                total_fn += result.false_negatives["seiz"]

            print(f"  {ref_file.name}: TP={result.true_positives.get('seiz', 0)}")

        except Exception as e:
            print(f"  Error in {ref_file.name}: {e}")

    print(f"\nAccumulated results:")
    print(f"  Total TP: {total_tp}")
    print(f"  Total FP: {total_fp}")
    print(f"  Total FN: {total_fn}")

    if total_tp + total_fn > 0:
        sensitivity = total_tp / (total_tp + total_fn) * 100
        print(f"  Sensitivity: {sensitivity:.4f}%")

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("EPOCH ALGORITHM FIX TEST")
    print("=" * 60)

    # Test single file
    success = test_single_file()

    if success:
        print("\n✅ Single file test PASSED!")

        # Test multiple files
        test_multiple_files()
    else:
        print("\n❌ Single file test FAILED!")
        sys.exit(1)