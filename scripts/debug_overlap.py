#!/usr/bin/env python3
"""Debug Overlap algorithm issues"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.models.annotations import AnnotationFile

# Test specific files that error
data_root = Path("data/csv_bi_parity/csv_bi_export_clean")

# Files that error with 'seiz'
error_files = [
    "aaaaaajy_s001_t000.csv_bi",
    "aaaaaajy_s002_t002.csv_bi",
]

scorer = OverlapScorer()

for filename in error_files:
    ref_file = data_root / "ref" / filename
    hyp_file = data_root / "hyp" / filename

    if not ref_file.exists():
        continue

    print(f"\nAnalyzing: {filename}")
    print("-" * 50)

    ref_ann = AnnotationFile.from_csv_bi(ref_file)
    hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

    # Check what labels exist
    ref_labels = set(e.label for e in ref_ann.events)
    hyp_labels = set(e.label for e in hyp_ann.events)

    print(f"Reference labels: {ref_labels}")
    print(f"Hypothesis labels: {hyp_labels}")

    # Score
    result = scorer.score(ref_ann.events, hyp_ann.events)

    print(f"Result hits keys: {result.hits.keys()}")
    print(f"Result misses keys: {result.misses.keys()}")
    print(f"Result false_alarms keys: {result.false_alarms.keys()}")

    # Check if seiz exists
    if "seiz" in result.hits:
        print(f"Seiz: TP={result.hits['seiz']}, FP={result.false_alarms.get('seiz', 0)}, FN={result.misses['seiz']}")
    else:
        print("NO SEIZ IN RESULTS - this is why it errors!")

    # What's actually in there?
    for label in result.hits:
        tp = result.hits[label]
        fp = result.false_alarms.get(label, 0)
        fn = result.misses.get(label, 0)
        print(f"{label}: TP={tp}, FP={fp}, FN={fn}")

# Now test aggregation across many files
print("\n" + "=" * 60)
print("Testing aggregation across 100 files...")

total_tp = 0
total_fp = 0
total_fn = 0
errors = 0

files = list((data_root / "ref").glob("*.csv_bi"))[:100]

for ref_file in files:
    hyp_file = data_root / "hyp" / ref_file.name

    try:
        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

        result = scorer.score(ref_ann.events, hyp_ann.events)

        # SAFE access with .get()
        total_tp += result.hits.get("seiz", 0)
        total_fp += result.false_alarms.get("seiz", 0)
        total_fn += result.misses.get("seiz", 0)

    except KeyError as e:
        errors += 1
        print(f"Error in {ref_file.name}: {e}")

print(f"\nResults from {len(files)} files ({errors} errors):")
print(f"TP: {total_tp}, FP: {total_fp}, FN: {total_fn}")

if total_tp + total_fn > 0:
    sensitivity = total_tp / (total_tp + total_fn) * 100
    print(f"Sensitivity: {sensitivity:.2f}%")

print("\nExpected from Alpha:")
print("TP: 253, FP: 536, FN: 822")
print("Sensitivity: 23.53%")