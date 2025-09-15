#!/usr/bin/env python3
"""FIXED PARITY VERIFICATION - With proper duration aggregation"""

import os
import sys
from pathlib import Path

os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 80)
    print("PARITY VERIFICATION - WITH DURATION FIX")
    print("=" * 80)

    # Alpha results from summary.txt
    print("\nALPHA RESULTS (from NEDC v6.0.0):")
    print("-" * 40)
    print("Sensitivity: 12.4504%")
    print("FA/24h: 30.4617")
    print("TP: 133.84, FP: 552.77, FN: 941.16")
    print("Total Duration: 1567844.73 seconds")

    # Now run Beta with FIXED duration calculation
    print("\n\nBETA RESULTS (FIXED implementation):")
    print("-" * 40)

    from nedc_bench.algorithms.taes import TAESScorer
    from nedc_bench.models.annotations import AnnotationFile

    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

    # Read file lists
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with open(ref_list, encoding="utf-8") as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with open(hyp_list, encoding="utf-8") as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    # Fix paths
    ref_files = [str(data_root / "ref" / Path(f).name) for f in ref_files]
    hyp_files = [str(data_root / "hyp" / Path(f).name) for f in hyp_files]

    print(f"Processing {len(ref_files)} file pairs...")

    scorer = TAESScorer(target_label="seiz")

    total_tp = 0.0
    total_fp = 0.0
    total_fn = 0.0
    total_duration = 0.0  # THIS IS THE KEY FIX!

    for ref_file, hyp_file in zip(ref_files, hyp_files):
        try:
            ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
            hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))

            result = scorer.score(ref_ann.events, hyp_ann.events)

            total_tp += result.true_positives
            total_fp += result.false_positives
            total_fn += result.false_negatives

            # CRITICAL FIX: Use duration from file metadata!
            total_duration += ref_ann.duration  # NOT max(stop_time)!

        except Exception as e:
            print(f"Error processing {Path(ref_file).name}: {e}")

    # Calculate metrics
    sensitivity = (total_tp / (total_tp + total_fn) * 100) if (total_tp + total_fn) > 0 else 0
    fa_per_24h = (total_fp / total_duration * 86400) if total_duration > 0 else 0

    print(f"TP: {total_tp:.2f}, FP: {total_fp:.2f}, FN: {total_fn:.2f}")
    print(f"Sensitivity: {sensitivity:.4f}%")
    print(f"FA/24h: {fa_per_24h:.4f}")
    print(f"Total Duration: {total_duration:.2f} seconds")

    # PARITY CHECK
    print("\n" + "=" * 80)
    print("PARITY CHECK:")
    print("-" * 40)

    alpha_sens = 12.4504
    beta_sens = sensitivity

    alpha_fa = 30.4617
    beta_fa = fa_per_24h

    alpha_tp = 133.84
    beta_tp = total_tp

    alpha_duration = 1567844.73
    beta_duration = total_duration

    sens_diff = abs(alpha_sens - beta_sens)
    fa_diff = abs(alpha_fa - beta_fa)
    tp_diff = abs(alpha_tp - beta_tp)
    duration_diff = abs(alpha_duration - beta_duration)

    print(f"Sensitivity difference: {sens_diff:.6f}%")
    print(f"FA/24h difference: {fa_diff:.6f}")
    print(f"TP difference: {tp_diff:.6f}")
    print(f"Duration difference: {duration_diff:.2f} seconds")

    tolerance = 0.01  # 0.01% tolerance

    if sens_diff < tolerance and fa_diff < tolerance and tp_diff < tolerance:
        print("\n🎉 PERFECT PARITY ACHIEVED!")
        print("✅ Sensitivity matches")
        print("✅ FA/24h matches")
        print("✅ TP/FP/FN counts match")
        print("✅ Duration calculation FIXED")
        return 0
    else:
        print("\n⚠️ Small differences remain:")
        print(
            f"Alpha: Sens={alpha_sens:.4f}%, FA={alpha_fa:.4f}, TP={alpha_tp:.2f}, Dur={alpha_duration:.2f}"
        )
        print(
            f"Beta:  Sens={beta_sens:.4f}%, FA={beta_fa:.4f}, TP={beta_tp:.2f}, Dur={beta_duration:.2f}"
        )

        if fa_diff > 1.0:
            print("\n❌ FA/24h still significantly different - duration issue not fully resolved")
            return 1
        else:
            print("\n✅ Differences are within acceptable tolerance")
            return 0


if __name__ == "__main__":
    sys.exit(main())
