#!/usr/bin/env python3
"""Compare Alpha vs Beta results for parity."""

import json
from pathlib import Path

def compare_results():
    """Compare SSOT_ALPHA.json vs SSOT_BETA.json"""

    # Load results
    with open("SSOT_ALPHA.json") as f:
        alpha = json.load(f)

    with open("SSOT_BETA.json") as f:
        beta = json.load(f)

    print("="*60)
    print("ALPHA vs BETA PARITY COMPARISON")
    print("="*60)

    for algo in ["taes", "epoch", "overlap", "dp"]:
        print(f"\n{algo.upper()} Algorithm:")
        print("-"*40)

        a = alpha[algo]
        b = beta[algo]

        # Calculate differences
        tp_diff = b["tp"] - a["tp"]
        fp_diff = b["fp"] - a["fp"]
        fn_diff = b["fn"] - a["fn"]

        # Calculate parity percentage
        if a["tp"] > 0:
            tp_parity = (b["tp"] / a["tp"]) * 100
        else:
            tp_parity = 100 if b["tp"] == 0 else 0

        print(f"  Alpha TP: {a['tp']:.2f}, Beta TP: {b['tp']:.2f}, Diff: {tp_diff:.2f} ({tp_parity:.2f}% match)")
        print(f"  Alpha FP: {a['fp']:.2f}, Beta FP: {b['fp']:.2f}, Diff: {fp_diff:.2f}")
        print(f"  Alpha FN: {a['fn']:.2f}, Beta FN: {b['fn']:.2f}, Diff: {fn_diff:.2f}")
        print(f"  Alpha Sens: {a['sensitivity']:.2f}%, Beta Sens: {b['sensitivity']:.2f}%")
        print(f"  Alpha FA/24h: {a['fa_per_24h']:.2f}, Beta FA/24h: {b['fa_per_24h']:.2f}")

        # Check if exact match
        if abs(tp_diff) < 0.01 and abs(fp_diff) < 0.01 and abs(fn_diff) < 0.01:
            print("  ✅ EXACT PARITY ACHIEVED!")
        elif abs(tp_diff) < 1 and abs(fp_diff) < 1 and abs(fn_diff) < 1:
            print("  ⚠️ Near parity (< 1 event difference)")
        else:
            print(f"  ❌ Parity mismatch: TP diff={tp_diff:.2f}")

if __name__ == "__main__":
    compare_results()