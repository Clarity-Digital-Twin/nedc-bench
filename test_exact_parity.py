#!/usr/bin/env python3
"""Test EXACT TAES implementation for perfect parity"""

from pathlib import Path
from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.algorithms.taes_exact import TAESExactScorer
from nedc_bench.models.annotations import AnnotationFile

# Test files
ref_file = "nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi"
hyp_file = "nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi"

# Run Alpha
print("Running Alpha (NEDC v6.0.0)...")
alpha = NEDCAlphaWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
alpha_result = alpha.evaluate(ref_file, hyp_file)
print(f"Alpha TAES Results:")
print(f"  TP: {alpha_result['taes']['true_positives']:.2f}")
print(f"  FP: {alpha_result['taes']['false_positives']:.2f}")
print(f"  FN: {alpha_result['taes']['false_negatives']:.2f}")
print(f"  Sensitivity: {alpha_result['taes']['sensitivity']:.6f}")
print(f"  Precision: {alpha_result['taes']['precision']:.6f}")

# Run Beta EXACT
print("\nRunning Beta EXACT...")
ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))

# Debug: Show events
print(f"  Total ref events: {len(ref_ann.events)}")
print(f"  Total hyp events: {len(hyp_ann.events)}")
print(f"  SEIZ refs: {len([e for e in ref_ann.events if e.label == 'seiz'])}")
print(f"  SEIZ hyps: {len([e for e in hyp_ann.events if e.label == 'seiz'])}")

scorer = TAESExactScorer(target_label="seiz")
beta_result = scorer.score(ref_ann.events, hyp_ann.events)
print(f"\nBeta EXACT Results:")
print(f"  TP: {beta_result.true_positives:.2f}")
print(f"  FP: {beta_result.false_positives:.2f}")
print(f"  FN: {beta_result.false_negatives:.2f}")
print(f"  Sensitivity: {beta_result.sensitivity:.6f}")
print(f"  Precision: {beta_result.precision:.6f}")

# Compare
print(f"\n{'='*50}")
print("PARITY CHECK:")
tp_match = abs(beta_result.true_positives - alpha_result['taes']['true_positives']) < 0.01
fp_match = abs(beta_result.false_positives - alpha_result['taes']['false_positives']) < 0.01
fn_match = abs(beta_result.false_negatives - alpha_result['taes']['false_negatives']) < 0.01

if tp_match and fp_match and fn_match:
    print("✅ PERFECT PARITY ACHIEVED!")
else:
    print("❌ Parity not achieved:")
    print(f"  TP diff: {beta_result.true_positives - alpha_result['taes']['true_positives']:.2f}")
    print(f"  FP diff: {beta_result.false_positives - alpha_result['taes']['false_positives']:.2f}")
    print(f"  FN diff: {beta_result.false_negatives - alpha_result['taes']['false_negatives']:.2f}")

# Test multi-ref overlap case
print(f"\n{'='*50}")
print("TEST CASE: One hyp spanning two refs")
from nedc_bench.models.annotations import EventAnnotation

refs = [
    EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0),
    EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0),
]
hyps = [
    EventAnnotation(start_time=5, stop_time=25, label="seiz", confidence=1.0),
]

result = scorer.score(refs, hyps)
print(f"  Refs: [0-10], [20-30]")
print(f"  Hyp:  [5-25] (spans both)")
print(f"  Result: TP={result.true_positives:.2f}, FP={result.false_positives:.2f}, FN={result.false_negatives:.2f}")
print(f"  Expected per NEDC: TP=0.50, FP=1.00, FN=1.50")
expected = abs(result.true_positives - 0.5) < 0.01 and abs(result.false_negatives - 1.5) < 0.01
print(f"  Match: {'✅' if expected else '❌'}")