#!/usr/bin/env python3
"""Test if IRA needs the same augmentation fix as Epoch."""

import json
import os
import sys
from pathlib import Path

os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import AnnotationFile, EventAnnotation
from nedc_bench.utils.params import load_nedc_params, map_event_label


def augment_events_full(events, file_duration, null_class="bckg"):
    """Augment events with background to fill ALL gaps (like NEDC does)."""
    if not events:
        return [EventAnnotation(
            channel="TERM",
            start_time=0.0,
            stop_time=file_duration,
            label=null_class,
            confidence=1.0
        )]

    augmented = []
    curr_time = 0.0

    for ev in sorted(events, key=lambda x: x.start_time):
        # Fill gap before this event
        if curr_time < ev.start_time:
            augmented.append(EventAnnotation(
                channel="TERM",
                start_time=curr_time,
                stop_time=ev.start_time,
                label=null_class,
                confidence=1.0
            ))
        augmented.append(ev)
        curr_time = ev.stop_time

    # Fill gap at end
    if curr_time < file_duration:
        augmented.append(EventAnnotation(
            channel="TERM",
            start_time=curr_time,
            stop_time=file_duration,
            label=null_class,
            confidence=1.0
        ))

    return augmented


def main():
    print("=" * 80)
    print("TESTING IRA WITH FULL AUGMENTATION")
    print("=" * 80)

    params = load_nedc_params()

    data_root = Path("data/csv_bi_parity/csv_bi_export_clean")
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with ref_list.open() as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with hyp_list.open() as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    ref_files = [data_root / "ref" / Path(f).name for f in ref_files]
    hyp_files = [data_root / "hyp" / Path(f).name for f in hyp_files]

    ira = IRAScorer()

    # Test both approaches
    agg_conf_without = {r: {c: 0 for c in ['seiz', 'bckg']} for r in ['seiz', 'bckg']}
    agg_conf_with = {r: {c: 0 for c in ['seiz', 'bckg']} for r in ['seiz', 'bckg']}

    print(f"Processing {len(ref_files)} files...")
    print("\nTesting first 100 files for quick comparison...")

    for i, (ref_file, hyp_file) in enumerate(zip(ref_files[:100], hyp_files[:100])):
        if i % 20 == 0:
            print(f"  Processed {i}/100...")

        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

        # Normalize labels
        for ev in ref_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)
        for ev in hyp_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)

        # WITHOUT full augmentation (current approach - only empty files)
        ref_events_without = ref_ann.events if ref_ann.events else [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=ref_ann.duration,
                          label=params.null_class, confidence=1.0)
        ]
        hyp_events_without = hyp_ann.events if hyp_ann.events else [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=hyp_ann.duration,
                          label=params.null_class, confidence=1.0)
        ]

        res_without = ira.score(
            ref_events_without, hyp_events_without,
            epoch_duration=params.epoch_duration,
            file_duration=ref_ann.duration,
            null_class=params.null_class
        )

        # WITH full augmentation (like NEDC)
        ref_events_with = augment_events_full(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_events_with = augment_events_full(hyp_ann.events, hyp_ann.duration, params.null_class)

        res_with = ira.score(
            ref_events_with, hyp_events_with,
            epoch_duration=params.epoch_duration,
            file_duration=ref_ann.duration,
            null_class=params.null_class
        )

        # Aggregate
        for rlab, cols in res_without.confusion_matrix.items():
            for clab, val in cols.items():
                if rlab in agg_conf_without and clab in agg_conf_without[rlab]:
                    agg_conf_without[rlab][clab] += val

        for rlab, cols in res_with.confusion_matrix.items():
            for clab, val in cols.items():
                if rlab in agg_conf_with and clab in agg_conf_with[rlab]:
                    agg_conf_with[rlab][clab] += val

    print("\n" + "=" * 80)
    print("RESULTS (first 100 files):")
    print("=" * 80)

    print("\nWITHOUT full augmentation (current):")
    print_confusion(agg_conf_without)
    kappa_without = compute_kappa(agg_conf_without, ['seiz', 'bckg'])
    print(f"Kappa: {kappa_without:.6f}")

    print("\nWITH full augmentation (like NEDC):")
    print_confusion(agg_conf_with)
    kappa_with = compute_kappa(agg_conf_with, ['seiz', 'bckg'])
    print(f"Kappa: {kappa_with:.6f}")

    print("\n" + "=" * 80)
    print("DIFFERENCES:")
    print("=" * 80)
    for r in ['seiz', 'bckg']:
        for c in ['seiz', 'bckg']:
            diff = agg_conf_with[r][c] - agg_conf_without[r][c]
            if diff != 0:
                print(f"  {r} -> {c}: {diff:+d}")

    print(f"\nKappa difference: {kappa_with - kappa_without:.6f}")

    if abs(kappa_with - kappa_without) > 1e-6:
        print("\n⚠️ AUGMENTATION AFFECTS IRA!")
        print("IRA needs the same fix as Epoch - fill ALL gaps with background")
    else:
        print("\n✅ Augmentation doesn't affect IRA on this subset")


def print_confusion(conf):
    """Print confusion matrix."""
    print("  Ref/Hyp:    seiz        bckg")
    for r in ['seiz', 'bckg']:
        print(f"     {r}:  {conf[r]['seiz']:7d}   {conf[r]['bckg']:7d}")


def compute_kappa(conf, labels):
    """Compute multi-class kappa."""
    sum_rows = {l: sum(conf[l].values()) for l in labels}
    sum_cols = {l: sum(conf[r][l] for r in labels) for l in labels}
    sum_m = sum(conf[l][l] for l in labels)
    sum_n = sum(sum_rows.values())
    sum_gc = sum(sum_rows[l] * sum_cols[l] for l in labels)

    num = sum_n * sum_m - sum_gc
    denom = sum_n * sum_n - sum_gc

    return float(num) / float(denom) if denom != 0 else 0.0


if __name__ == "__main__":
    main()