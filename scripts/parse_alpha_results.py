#!/usr/bin/env python3
"""Parse Alpha (NEDC v6.0.0) results from summary.txt and per-algo files.

Outputs SSOT_ALPHA.json with per-algorithm metrics that align with how
our Beta implementation reports totals:
- TAES/DP/Overlap/Epoch: tp, fp, fn, sensitivity, fa_per_24h
- IRA: multi_class_kappa, per_label_kappa

Notes:
- Epoch FA/24h is per NEDC: scale FP by epoch_duration before rate.
- All values are parsed from NEDC summary to avoid recomputation drift.
"""

import json
import re
from pathlib import Path


def parse_alpha_results() -> dict:
    """Parse NEDC output to extract totals for all algorithms.

    We prefer parsing summary.txt for consistency (also contains IRA).
    """
    nedc_output = Path("nedc_eeg_eval/v6.0.0/output")
    summary_path = nedc_output / "summary.txt"
    if not summary_path.exists():
        raise FileNotFoundError(f"NEDC summary not found: {summary_path}")

    text = summary_path.read_text(encoding="utf-8", errors="ignore")

    def section(block_title: str) -> str:
        pat = rf"==============================\n{re.escape(block_title)}.*?\n(.*?)\n=============================="
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if not m:
            # Fallback: try non-greedy between title and next separator
            pat2 = rf"{re.escape(block_title)}.*?\n(.*?)(?:\n={(10,)}|\Z)"
            m = re.search(pat2, text, re.DOTALL | re.IGNORECASE)
        return m.group(1) if m else ""

    def parse_label_block(sect: str, label: str) -> dict:
        """Extract key:value pairs under "LABEL: <label>" until next label/summary.

        We parse across blank lines to include TP/FP/FN and False Alarm Rate lines.
        """
        lab_pat = rf"^\s*LABEL:\s*{label}\b.*?\n(.*?)(?=\n\s*LABEL:|\n\s*SUMMARY:|\Z)"
        m = re.search(lab_pat, sect, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        block = m.group(1) if m else ""
        return {
            k: v
            for k, v in (
                re.findall(r"^\s*([A-Za-z \(\)]+):\s+([0-9\.]+)", block, re.MULTILINE)
                if block
                else []
            )
        }

    results: dict[str, dict] = {}

    # ---------- DP ----------
    dp_sec = section("NEDC DP ALIGNMENT SCORING SUMMARY")
    dp_seiz = parse_label_block(dp_sec, "SEIZ")
    if dp_seiz:
        tp = float(dp_seiz.get("Hits", 0))
        fp = float(dp_seiz.get("False Alarms", 0))
        fn = float(dp_seiz.get("Misses", 0))
        fa = float(dp_seiz.get("False Alarm Rate", 0.0))
        sens = 100.0 * tp / (tp + fn) if (tp + fn) > 0 else 0.0
        results["dp"] = {"tp": tp, "fp": fp, "fn": fn, "sensitivity": sens, "fa_per_24h": fa}

    # ---------- Epoch ----------
    ep_sec = section("NEDC EPOCH SCORING SUMMARY")
    # Pull TP/FP/FN from the "PER LABEL RESULTS -> LABEL: SEIZ" block
    # True Positives (TP), False Positives (FP), False Negatives (FN)
    ep_seiz = parse_label_block(ep_sec, "SEIZ")
    if ep_seiz:
        tp = float(ep_seiz.get("True Positives (TP)", 0))
        fp = float(ep_seiz.get("False Positives (FP)", 0))
        fn = float(ep_seiz.get("False Negatives (FN)", 0))
        fa = float(ep_seiz.get("False Alarm Rate", 0.0))
        sens = 100.0 * tp / (tp + fn) if (tp + fn) > 0 else 0.0
        results["epoch"] = {"tp": tp, "fp": fp, "fn": fn, "sensitivity": sens, "fa_per_24h": fa}

    # ---------- Overlap ----------
    ov_sec = section("NEDC OVERLAP SCORING SUMMARY")
    ov_seiz = parse_label_block(ov_sec, "SEIZ")
    if ov_seiz:
        tp = float(ov_seiz.get("Hits", 0))
        fp = float(ov_seiz.get("False Alarms", 0))
        fn = float(ov_seiz.get("Misses", 0))
        fa = float(ov_seiz.get("False Alarm Rate", 0.0))
        sens = 100.0 * tp / (tp + fn) if (tp + fn) > 0 else 0.0
        results["overlap"] = {"tp": tp, "fp": fp, "fn": fn, "sensitivity": sens, "fa_per_24h": fa}

    # ---------- TAES ----------
    ta_sec = section("NEDC TAES SCORING SUMMARY")
    ta_seiz = parse_label_block(ta_sec, "SEIZ")
    if ta_seiz:
        tp = float(ta_seiz.get("Hits", 0))
        fp = float(ta_seiz.get("False Alarms", 0))
        fn = float(ta_seiz.get("Misses", 0))
        fa = float(ta_seiz.get("False Alarm Rate", 0.0))
        sens = 100.0 * tp / (tp + fn) if (tp + fn) > 0 else 0.0
        results["taes"] = {"tp": tp, "fp": fp, "fn": fn, "sensitivity": sens, "fa_per_24h": fa}

    # ---------- IRA ----------
    ira_sec = section("NEDC INTER-RATER AGREEMENT SUMMARY")
    if ira_sec:
        # Multi-Class Kappa
        mk = re.search(r"Multi-Class Kappa:\s*([0-9\.]+)", ira_sec)
        multi = float(mk.group(1)) if mk else 0.0
        # Per-label kappa lines: "Label: seiz   Kappa:  0.1887"
        per: dict[str, float] = {}
        for lab, kv in re.findall(r"Label:\s*(\w+)\s*Kappa:\s*([0-9\.]+)", ira_sec):
            per[lab.lower()] = float(kv)
        results["ira"] = {"multi_class_kappa": multi, "per_label_kappa": per}

    # Save results
    Path("SSOT_ALPHA.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Friendly print
    print("Alpha Results (parsed from summary.txt):")
    for algo, metrics in results.items():
        print(f"\n{algo.upper()}:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")

    return results


if __name__ == "__main__":
    parse_alpha_results()
