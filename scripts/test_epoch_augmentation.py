#!/usr/bin/env python3
"""Test if the Epoch algorithm difference is due to augmentation handling.

NEDC explicitly augments both ref and hyp annotations to file duration with
background events. Our Beta uses null_class when no event is found.

This script tests if explicitly augmenting fixes the 9 TP difference.
"""

import json
import os
import sys
from pathlib import Path
from typing import List

# Setup paths
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"
sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import AnnotationFile, EventAnnotation
from nedc_bench.utils.params import load_nedc_params, map_event_label


def augment_events_nedc_style(
    events: List[EventAnnotation], file_duration: float, null_class: str = "bckg"
) -> List[EventAnnotation]:
    """Augment events with background like NEDC does.

    NEDC fills all gaps with background events so the annotation
    spans from 0 to file_duration continuously.
    """
    if not events:
        # Empty annotation - fill entire duration with background
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
        # Fill gap before this event if needed
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

        # Add the actual event
        augmented.append(ev)
        curr_time = ev.stop_time

    # Fill gap at end if needed
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


def run_epoch_with_augmentation(ref_file: Path, hyp_file: Path, params):
    """Run Epoch with NEDC-style augmentation."""
    ref_ann = AnnotationFile.from_csv_bi(ref_file)
    hyp_ann = AnnotationFile.from_csv_bi(hyp_file)

    # Normalize labels
    for ev in ref_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)
    for ev in hyp_ann.events:
        ev.label = map_event_label(ev.label, params.label_map)

    # CRITICAL: Augment like NEDC does!
    ref_augmented = augment_events_nedc_style(ref_ann.events, ref_ann.duration, params.null_class)
    hyp_augmented = augment_events_nedc_style(hyp_ann.events, hyp_ann.duration, params.null_class)

    # Now run Epoch on augmented events
    scorer = EpochScorer(epoch_duration=params.epoch_duration, null_class=params.null_class)

    result = scorer.score(ref_augmented, hyp_augmented, file_duration=ref_ann.duration)

    return result


def main():
    print("=" * 80)
    print("TESTING EPOCH WITH NEDC-STYLE AUGMENTATION")
    print("=" * 80)

    params = load_nedc_params()

    # Load file lists
    data_root = Path("data/csv_bi_parity/csv_bi_export_clean")
    ref_list = data_root / "lists" / "ref.list"
    hyp_list = data_root / "lists" / "hyp.list"

    with ref_list.open() as f:
        ref_files = [line.strip() for line in f if line.strip()]
    with hyp_list.open() as f:
        hyp_files = [line.strip() for line in f if line.strip()]

    # Convert to full paths
    ref_files = [data_root / "ref" / Path(f).name for f in ref_files]
    hyp_files = [data_root / "hyp" / Path(f).name for f in hyp_files]

    print(f"Testing on all {len(ref_files)} file pairs...")
    print("This will take a few minutes...")

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for i, (ref_file, hyp_file) in enumerate(zip(ref_files, hyp_files)):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(ref_files)} files...")

        result = run_epoch_with_augmentation(ref_file, hyp_file, params)

        # Accumulate SEIZ metrics
        tp = result.true_positives.get("seiz", 0)
        fp = result.false_positives.get("seiz", 0)
        fn = result.false_negatives.get("seiz", 0)

        total_tp += tp
        total_fp += fp
        total_fn += fn

    print(f"\nCompleted processing {len(ref_files)} files")
    print("\n" + "=" * 80)
    print("RESULTS WITH NEDC-STYLE AUGMENTATION:")
    print("=" * 80)
    print(f"  TP: {total_tp}")
    print(f"  FP: {total_fp}")
    print(f"  FN: {total_fn}")

    # Compare with known values
    print("\n" + "=" * 80)
    print("COMPARISON WITH KNOWN VALUES:")
    print("=" * 80)

    # Load SSOT files
    with open("SSOT_ALPHA.json") as f:
        alpha = json.load(f)
    with open("SSOT_BETA.json") as f:
        beta = json.load(f)

    print("\nAlpha (NEDC v6.0.0):")
    print(f"  TP: {alpha['epoch']['tp']}")
    print(f"  FP: {alpha['epoch']['fp']}")
    print(f"  FN: {alpha['epoch']['fn']}")

    print("\nBeta (without augmentation):")
    print(f"  TP: {beta['epoch']['tp']}")
    print(f"  FP: {beta['epoch']['fp']}")
    print(f"  FN: {beta['epoch']['fn']}")

    print("\nBeta (WITH augmentation):")
    print(f"  TP: {total_tp}")
    print(f"  FP: {total_fp}")
    print(f"  FN: {total_fn}")

    # Check if we achieved parity
    alpha_tp = int(alpha["epoch"]["tp"])
    alpha_fp = int(alpha["epoch"]["fp"])
    alpha_fn = int(alpha["epoch"]["fn"])

    tp_diff = total_tp - alpha_tp
    fp_diff = total_fp - alpha_fp
    fn_diff = total_fn - alpha_fn

    print("\n" + "=" * 80)
    print("PARITY CHECK:")
    print("=" * 80)
    print(f"  TP difference: {tp_diff:+d}")
    print(f"  FP difference: {fp_diff:+d}")
    print(f"  FN difference: {fn_diff:+d}")

    if tp_diff == 0 and fp_diff == 0 and fn_diff == 0:
        print("\n🎉 EXACT PARITY ACHIEVED! The augmentation hypothesis was CORRECT!")
    else:
        print("\n❌ Still have differences. Augmentation alone didn't fix it.")
        print("   Need to investigate further...")


if __name__ == "__main__":
    main()
