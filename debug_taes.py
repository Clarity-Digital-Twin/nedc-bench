#!/usr/bin/env python3
"""Debug TAES scoring discrepancy"""

from pathlib import Path
from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile

# Test on single file
ref_file = "nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi"
hyp_file = "nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi"

# Run Alpha (wrapper)
print("Running Alpha...")
alpha = NEDCAlphaWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
alpha_result = alpha.evaluate(ref_file, hyp_file)
print(f"Alpha TAES Results:")
print(f"  TP: {alpha_result['taes']['true_positives']}")
print(f"  FP: {alpha_result['taes']['false_positives']}")
print(f"  FN: {alpha_result['taes']['false_negatives']}")
print(f"  Sensitivity: {alpha_result['taes']['sensitivity']}")

# Run Beta
print("\nRunning Beta...")
ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))
print(f"  Ref events: {len(ref_ann.events)}")
print(f"  Hyp events: {len(hyp_ann.events)}")

# Show first few events
print("\nFirst 3 ref events:")
for e in ref_ann.events[:3]:
    print(f"  {e.label}: {e.start_time:.2f} - {e.stop_time:.2f}")

print("\nFirst 3 hyp events:")
for e in hyp_ann.events[:3]:
    print(f"  {e.label}: {e.start_time:.2f} - {e.stop_time:.2f}")

scorer = TAESScorer()
beta_result = scorer.score(ref_ann.events, hyp_ann.events)
print(f"\nBeta TAES Results:")
print(f"  TP: {beta_result.true_positives:.2f}")
print(f"  FP: {beta_result.false_positives:.2f}")
print(f"  FN: {beta_result.false_negatives:.2f}")
print(f"  Sensitivity: {beta_result.sensitivity:.4f}")

# Compare
print(f"\nDiscrepancy:")
print(f"  TP diff: {beta_result.true_positives - alpha_result['taes']['true_positives']:.2f}")
print(f"  FP diff: {beta_result.false_positives - alpha_result['taes']['false_positives']:.2f}")
print(f"  FN diff: {beta_result.false_negatives - alpha_result['taes']['false_negatives']:.2f}")