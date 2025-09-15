#!/usr/bin/env python3
"""Debug the IRA kappa difference between Alpha and Beta."""

import os
import sys
from pathlib import Path

os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import AnnotationFile, EventAnnotation
from nedc_bench.utils.params import load_nedc_params, map_event_label


def main():
    print("=" * 80)
    print("IRA KAPPA DIFFERENCE INVESTIGATION")
    print("=" * 80)

    params = load_nedc_params()

    data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with ref_list.open(encoding="utf-8") as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with hyp_list.open(encoding="utf-8") as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    ref_files = [str(data_root / "ref" / Path(f).name) for f in ref_files]
    hyp_files = [str(data_root / "hyp" / Path(f).name) for f in hyp_files]

    ira = IRAScorer()

    # Aggregate confusion across files
    agg_labels = sorted({params.null_class, "seiz", "bckg"})
    agg_conf = {r: {c: 0 for c in agg_labels} for r in agg_labels}

    print(f"Processing {len(ref_files)} file pairs...")

    # Track files with events
    files_with_events = 0
    files_without_events = 0

    for i, (ref_file, hyp_file) in enumerate(zip(ref_files, hyp_files)):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(ref_files)} files...")

        ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))

        # Normalize labels
        for ev in ref_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)
        for ev in hyp_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)

        # Check if files have events
        if not ref_ann.events and not hyp_ann.events:
            files_without_events += 1
        else:
            files_with_events += 1

        # Handle empty annotations (like run_beta_ira.py does)
        if not ref_ann.events:
            ref_ann.events = [
                EventAnnotation(
                    channel="TERM",
                    start_time=0.0,
                    stop_time=ref_ann.duration,
                    label=params.null_class,
                    confidence=1.0,
                )
            ]
        if not hyp_ann.events:
            hyp_ann.events = [
                EventAnnotation(
                    channel="TERM",
                    start_time=0.0,
                    stop_time=hyp_ann.duration,
                    label=params.null_class,
                    confidence=1.0,
                )
            ]

        # Per-file confusion
        res = ira.score(
            ref_ann.events,
            hyp_ann.events,
            epoch_duration=params.epoch_duration,
            file_duration=ref_ann.duration,
            null_class=params.null_class,
        )

        # Aggregate
        for rlab, cols in res.confusion_matrix.items():
            for clab, val in cols.items():
                agg_conf.setdefault(rlab, {}).setdefault(clab, 0)
                agg_conf[rlab][clab] += int(val)

    print(f"\nTotal files with events: {files_with_events}")
    print(f"Total files without events: {files_without_events}")

    # Print our aggregated confusion matrix
    print("\n" + "=" * 80)
    print("BETA AGGREGATED CONFUSION MATRIX:")
    print("=" * 80)
    print("  Ref/Hyp:         seiz                  bckg")
    for ref_label in ["seiz", "bckg"]:
        row_sum = sum(agg_conf.get(ref_label, {}).values())
        print(f"     {ref_label}:", end="")
        for hyp_label in ["seiz", "bckg"]:
            count = agg_conf.get(ref_label, {}).get(hyp_label, 0)
            pct = (count / row_sum * 100) if row_sum > 0 else 0
            print(f"    {count:8.0f} ({pct:6.2f}%)", end="")
        print()

    # Compare with NEDC's matrix
    print("\n" + "=" * 80)
    print("NEDC (ALPHA) CONFUSION MATRIX:")
    print("=" * 80)
    print("  Ref/Hyp:         seiz                  bckg")
    print("     seiz:    33704.00 ( 11.86%)   250459.00 ( 88.14%)")
    print("     bckg:    18816.00 (  0.31%)  5968398.00 ( 99.69%)")

    # Calculate differences
    nedc_conf = {"seiz": {"seiz": 33704, "bckg": 250459}, "bckg": {"seiz": 18816, "bckg": 5968398}}

    print("\n" + "=" * 80)
    print("DIFFERENCES (Beta - Alpha):")
    print("=" * 80)
    for ref_label in ["seiz", "bckg"]:
        for hyp_label in ["seiz", "bckg"]:
            beta_val = agg_conf.get(ref_label, {}).get(hyp_label, 0)
            alpha_val = nedc_conf.get(ref_label, {}).get(hyp_label, 0)
            diff = beta_val - alpha_val
            if diff != 0:
                print(f"  {ref_label} -> {hyp_label}: {diff:+d}")

    # Compute kappas on both matrices
    labels = sorted(agg_conf.keys())

    # Beta kappa
    beta_multi = ira._compute_multi_class_kappa(agg_conf, labels)

    # Alpha kappa (from NEDC matrix)
    alpha_multi = compute_kappa_from_matrix(nedc_conf, ["seiz", "bckg"])

    print("\n" + "=" * 80)
    print("KAPPA VALUES:")
    print("=" * 80)
    print(f"Alpha (from NEDC matrix): {alpha_multi:.20f}")
    print(f"Beta (our calculation):   {beta_multi:.20f}")
    print(f"Difference:               {beta_multi - alpha_multi:.20f}")
    print(f"\nAlpha rounded to 4 dec:   {alpha_multi:.4f}")
    print(f"Beta rounded to 4 dec:    {beta_multi:.4f}")


def compute_kappa_from_matrix(conf, labels):
    """Compute multi-class kappa from confusion matrix."""
    # Row and column sums
    sum_rows = {}
    sum_cols = {}
    for label in labels:
        sum_rows[label] = sum(conf.get(label, {}).values())
        sum_cols[label] = sum(conf.get(lbl, {}).get(label, 0) for lbl in labels)

    # Diagonal sum
    sum_m = sum(conf.get(label, {}).get(label, 0) for label in labels)

    # Total count
    sum_n = sum(sum_rows.values())

    # Sum of products of marginals
    sum_gc = sum(sum_rows[label] * sum_cols[label] for label in labels)

    # Compute kappa
    num = sum_n * sum_m - sum_gc
    denom = sum_n * sum_n - sum_gc

    if denom == 0:
        return 1.0 if num == 0 else 0.0

    return float(num) / float(denom)


if __name__ == "__main__":
    main()
