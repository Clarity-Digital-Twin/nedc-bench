#!/usr/bin/env python3
"""Run Beta batch - our implementation totals ONLY, no hardcoded bullshit."""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup paths
os.environ["NEDC_NFC"] = str(Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0")
os.environ["PYTHONPATH"] = f"{os.environ['NEDC_NFC']}/lib:{os.environ.get('PYTHONPATH', '')}"

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ultimate_parity_test import run_all_beta_algorithms
from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.utils.params import load_nedc_params, map_event_label


def main():
    """Run Beta algorithms and save SSOT results."""
    print("=" * 60)
    print("Running Beta (Our Implementation) Batch")
    print(f"Time: {datetime.now()}")
    print("=" * 60)

    # Run all Beta algorithms
    print("\nProcessing 1832 file pairs...")
    print("This will take several minutes...")

    beta_results_raw = run_all_beta_algorithms()

    # Convert to clean dictionary format
    beta_results = {}
    for algo_name, result in beta_results_raw.items():
        beta_results[algo_name] = {
            "tp": result.tp,
            "fp": result.fp,
            "fn": result.fn,
            "sensitivity": result.sensitivity,
            "fa_per_24h": result.fa_per_24h,
            "name": result.name
        }

        print(f"\n{algo_name.upper()}:")
        print(f"  TP: {result.tp:.2f}")
        print(f"  FP: {result.fp:.2f}")
        print(f"  FN: {result.fn:.2f}")
        print(f"  Sensitivity: {result.sensitivity:.4f}%")
        print(f"  FA/24h: {result.fa_per_24h:.4f}")

    # Additionally compute IRA (kappa-based) to complete the 5th algorithm
    try:
        print("\nComputing IRA (Inter-Rater Agreement) totals...")
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

        for ref_file, hyp_file in zip(ref_files, hyp_files):
            ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
            hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))
            # Normalize labels
            for ev in ref_ann.events:
                ev.label = map_event_label(ev.label, params.label_map)
            for ev in hyp_ann.events:
                ev.label = map_event_label(ev.label, params.label_map)
            # Per-file confusion then add to aggregate
            res = ira.score(
                ref_ann.events,
                hyp_ann.events,
                epoch_duration=params.epoch_duration,
                file_duration=ref_ann.duration,
                null_class=params.null_class,
            )
            # Ensure keys consistency
            for rlab, cols in res.confusion_matrix.items():
                for clab, val in cols.items():
                    agg_conf.setdefault(rlab, {}).setdefault(clab, 0)
                    agg_conf[rlab][clab] += int(val)

        # Compute kappas on aggregated confusion
        multi = ira._compute_multi_class_kappa(agg_conf, sorted(agg_conf.keys()))  # type: ignore[attr-defined]
        per = {
            lab: ira._compute_label_kappa(agg_conf, lab, sorted(agg_conf.keys()))  # type: ignore[attr-defined]
            for lab in sorted(agg_conf.keys())
        }
        beta_results["ira"] = {
            "multi_class_kappa": multi,
            "per_label_kappa": per,
            "name": "IRA",
        }
        print(f"IRA multi_class_kappa: {multi:.4f}")
    except Exception as e:
        print(f"Warning: IRA computation failed: {e}")

    # Save as JSON
    output_file = Path("SSOT_BETA.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(beta_results, f, indent=2, default=str)

    print(f"\n✅ Beta results saved to: {output_file}")
    print("=" * 60)

    return beta_results


if __name__ == "__main__":
    main()
