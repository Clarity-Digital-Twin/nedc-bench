#!/usr/bin/env python3
"""Debug why Epoch numbers are off by factor of 4"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import AnnotationFile

# Alpha expects:
# TP=33704, FP=18816, FN=250459

# Beta gets:
# TP=8409, FP=4715, FN=62624

# Ratios:
print("Scaling Analysis:")
print(f"TP ratio: 33704 / 8409 = {33704 / 8409:.2f}")
print(f"FP ratio: 18816 / 4715 = {18816 / 4715:.2f}")
print(f"FN ratio: 250459 / 62624 = {250459 / 62624:.2f}")

print("\nThis is EXACTLY 4x! Suggests epoch_duration issue.")
print()

# Test with different epoch durations
data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

ref_list = data_root / "lists" / "ref.list"
hyp_list = data_root / "lists" / "hyp.list"

with open(ref_list) as f:
    ref_files = [line.strip() for line in f if line.strip()][:100]  # Test 100 files

with open(hyp_list) as f:
    hyp_files = [line.strip() for line in f if line.strip()][:100]

# Fix paths
ref_files = [str(data_root / "ref" / Path(f).name) for f in ref_files]
hyp_files = [str(data_root / "hyp" / Path(f).name) for f in hyp_files]

for epoch_duration in [0.25, 1.0, 4.0]:
    print(f"\nTesting with epoch_duration = {epoch_duration} seconds:")
    print("-" * 50)

    scorer = EpochScorer(epoch_duration=epoch_duration)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for ref_file, hyp_file in zip(ref_files, hyp_files):
        try:
            ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
            hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))

            result = scorer.score(ref_ann.events, hyp_ann.events, ref_ann.duration)

            if "seiz" in result.true_positives:
                total_tp += result.true_positives["seiz"]
                total_fp += result.false_positives["seiz"]
                total_fn += result.false_negatives["seiz"]

        except Exception:
            pass

    print(f"  TP: {total_tp}")
    print(f"  FP: {total_fp}")
    print(f"  FN: {total_fn}")

    if total_tp + total_fn > 0:
        sensitivity = total_tp / (total_tp + total_fn) * 100
        print(f"  Sensitivity: {sensitivity:.4f}%")

    # Check if this matches Alpha ratio
    if epoch_duration == 0.25:
        print("\n  Projected full dataset (x18.32):")
        print(f"    TP: {total_tp * 18.32:.0f} (target: 33704)")
        print(f"    FP: {total_fp * 18.32:.0f} (target: 18816)")
        print(f"    FN: {total_fn * 18.32:.0f} (target: 250459)")

print("\n" + "=" * 60)
print("CONCLUSION: NEDC likely uses 0.25 second epochs (250ms)!")
print("This would give 4x more epochs than 1-second epochs.")
