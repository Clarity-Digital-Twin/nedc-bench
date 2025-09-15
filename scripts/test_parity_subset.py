#!/usr/bin/env python3
"""Quick parity test on subset of files"""

import os
import sys
from pathlib import Path

os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from nedc_bench.algorithms.dp_alignment import DPAligner
from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.utils.params import load_nedc_params, map_event_label

data_root = Path(__file__).parent.parent / "data" / "csv_bi_parity" / "csv_bi_export_clean"

# Read file lists
ref_list = data_root / "lists" / "ref.list"
hyp_list = data_root / "lists" / "hyp.list"

with ref_list.open(encoding="utf-8") as f:
    ref_files = [line.strip() for line in f if line.strip()][:10]  # TEST ONLY 10 FILES
with hyp_list.open(encoding="utf-8") as f:
    hyp_files = [line.strip() for line in f if line.strip()][:10]

ref_files = [str(data_root / "ref" / Path(f).name) for f in ref_files]
hyp_files = [str(data_root / "hyp" / Path(f).name) for f in hyp_files]

print(f"Testing {len(ref_files)} file pairs...")

params = load_nedc_params()

# Test each algorithm
for algo_name in ["taes", "epoch", "ovlp", "dp"]:
    print(f"\nTesting {algo_name.upper()}...")

    if algo_name == "taes":
        scorer = TAESScorer(target_label="seiz")
    elif algo_name == "epoch":
        scorer = EpochScorer(epoch_duration=params.epoch_duration, null_class=params.null_class)
    elif algo_name == "ovlp":
        scorer = OverlapScorer()
    elif algo_name == "dp":
        scorer = DPAligner()

    try:
        ref_ann = AnnotationFile.from_csv_bi(Path(ref_files[0]))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_files[0]))

        # Map labels
        for ev in ref_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)
        for ev in hyp_ann.events:
            ev.label = map_event_label(ev.label, params.label_map)

        if algo_name == "taes":
            result = scorer.score(ref_ann.events, hyp_ann.events)
            print(
                f"  TP={result.true_positives:.2f}, FP={result.false_positives:.2f}, FN={result.false_negatives:.2f}"
            )
        elif algo_name == "epoch":
            result = scorer.score(ref_ann.events, hyp_ann.events, ref_ann.duration)
            if "seiz" in result.true_positives:
                print(
                    f"  TP={result.true_positives['seiz']}, FP={result.false_positives['seiz']}, FN={result.false_negatives['seiz']}"
                )
        elif algo_name == "ovlp":
            result = scorer.score(ref_ann.events, hyp_ann.events)
            print(
                f"  TP={result.hits.get('seiz', 0)}, FP={result.false_alarms.get('seiz', 0)}, FN={result.misses.get('seiz', 0)}"
            )
        elif algo_name == "dp":
            # Convert to sequences
            n_epochs = int(np.ceil(ref_ann.duration / params.epoch_duration))
            ref_seq = [params.null_class] * n_epochs
            hyp_seq = [params.null_class] * n_epochs

            for event in ref_ann.events:
                start_epoch = int(event.start_time / params.epoch_duration)
                end_epoch = int(np.ceil(event.stop_time / params.epoch_duration))
                for i in range(start_epoch, min(end_epoch, n_epochs)):
                    ref_seq[i] = event.label

            for event in hyp_ann.events:
                start_epoch = int(event.start_time / params.epoch_duration)
                end_epoch = int(np.ceil(event.stop_time / params.epoch_duration))
                for i in range(start_epoch, min(end_epoch, n_epochs)):
                    hyp_seq[i] = event.label

            result = scorer.align(ref_seq, hyp_seq)
            print(
                f"  TP={result.true_positives}, FP={result.false_positives}, FN={result.false_negatives}"
            )

        print("  SUCCESS")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone!")
