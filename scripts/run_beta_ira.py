#!/usr/bin/env python3
"""Compute Beta IRA (kappa) across the dataset and update SSOT_BETA.json."""

import json
import os
import sys
from pathlib import Path

# Ensure local imports work like other scripts
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import AnnotationFile, EventAnnotation
from nedc_bench.utils.params import load_nedc_params, map_event_label


def main():
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

    # Aggregate confusion across files by summing per-file confusion matrices
    agg_labels = sorted({params.null_class, "seiz", "bckg"})
    agg_conf = {r: {c: 0 for c in agg_labels} for r in agg_labels}

    def augment_events_full(events, file_duration, null_class):
        """Augment events with background to fill ALL gaps (like NEDC does)."""
        if not events:
            return [
                EventAnnotation(
                    channel="TERM",
                    start_time=0.0,
                    stop_time=file_duration,
                    label=null_class,
                    confidence=1.0,
                )
            ]

        augmented = []
        curr_time = 0.0

        for ev in sorted(events, key=lambda x: x.start_time):
            # Fill gap before this event
            if curr_time < ev.start_time:
                augmented.append(
                    EventAnnotation(
                        channel="TERM",
                        start_time=curr_time,
                        stop_time=ev.start_time,
                        label=null_class,
                        confidence=1.0,
                    )
                )
            augmented.append(ev)
            curr_time = ev.stop_time

        # Fill gap at end
        if curr_time < file_duration:
            augmented.append(
                EventAnnotation(
                    channel="TERM",
                    start_time=curr_time,
                    stop_time=file_duration,
                    label=null_class,
                    confidence=1.0,
                )
            )

        return augmented

    for ref_file, hyp_file in zip(ref_files, hyp_files, strict=False):
        ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))
        # Normalize labels
        for ev in ref_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)
        for ev in hyp_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)

        # CRITICAL FIX: Augment ALL gaps with background (like NEDC does)
        # This fixes the 9/13 difference that caused 0.1887 vs 0.1888 kappa
        ref_augmented = augment_events_full(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_augmented = augment_events_full(hyp_ann.events, hyp_ann.duration, params.null_class)

        # Per-file confusion then add to aggregate
        res = ira.score(
            ref_augmented,  # Augmented events
            hyp_augmented,  # Augmented events
            epoch_duration=params.epoch_duration,
            file_duration=ref_ann.duration,
            null_class=params.null_class,
        )
        for rlab, cols in res.confusion_matrix.items():
            for clab, val in cols.items():
                agg_conf.setdefault(rlab, {}).setdefault(clab, 0)
                agg_conf[rlab][clab] += int(val)

    # Compute kappas on aggregated confusion
    labels = sorted(agg_conf.keys())
    multi = ira._compute_multi_class_kappa(agg_conf, labels)  # type: ignore[attr-defined]
    per = {lab: ira._compute_label_kappa(agg_conf, lab, labels) for lab in labels}  # type: ignore[attr-defined]

    # Load existing SSOT_BETA.json and update
    ssot_path = Path("SSOT_BETA.json")
    data = json.loads(ssot_path.read_text(encoding="utf-8")) if ssot_path.exists() else {}
    data["ira"] = {
        "multi_class_kappa": multi,
        "per_label_kappa": per,
        "name": "IRA",
    }
    ssot_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print("IRA updated in SSOT_BETA.json")
    print(f"  multi_class_kappa: {multi:.4f}")
    for lab, kv in per.items():
        print(f"  kappa[{lab}]: {kv:.4f}")


if __name__ == "__main__":
    main()
