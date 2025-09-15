#!/usr/bin/env python3
"""Debug the parity calculation to understand where differences come from."""

# Exact values from our debugging
alpha_tp = 133.84137545872732744101
beta_tp = 133.84137545872732744101

alpha_fp = 552.76890202314120870142
beta_fp = 552.76890202314120870142

alpha_fn = 941.15862454127307046292
beta_fn = 941.15862454127307046292

print("Testing different ways of calculating differences:")
print("=" * 60)

# Method 1: Direct subtraction
print("\n1. Direct subtraction (what we do in debug script):")
print(f"   TP diff: {beta_tp - alpha_tp:.20f}")
print(f"   FP diff: {beta_fp - alpha_fp:.20f}")
print(f"   FN diff: {beta_fn - alpha_fn:.20f}")

# Method 2: abs() like in ultimate_parity_test.py
print("\n2. Using abs() (like ultimate_parity_test.py):")
print(f"   TP diff: {abs(alpha_tp - beta_tp):.20f}")
print(f"   FP diff: {abs(alpha_fp - beta_fp):.20f}")
print(f"   FN diff: {abs(alpha_fn - beta_fn):.20f}")

# Method 3: What if values are slightly different when hardcoded?
# This is what's in get_alpha_metrics() in ultimate_parity_test.py
hardcoded_alpha_tp = 133.84
hardcoded_alpha_fp = 552.77
hardcoded_alpha_fn = 941.16

print("\n3. Using hardcoded rounded values from get_alpha_metrics():")
print(f"   Hardcoded Alpha: TP={hardcoded_alpha_tp}, FP={hardcoded_alpha_fp}, FN={hardcoded_alpha_fn}")
print(f"   Actual Alpha:    TP={alpha_tp:.2f}, FP={alpha_fp:.2f}, FN={alpha_fn:.2f}")
print(f"   Diff from hardcoded:")
print(f"     TP: {abs(hardcoded_alpha_tp - alpha_tp):.20f}")
print(f"     FP: {abs(hardcoded_alpha_fp - alpha_fp):.20f}")
print(f"     FN: {abs(hardcoded_alpha_fn - alpha_fn):.20f}")

# Check the actual hardcoded values in get_alpha_metrics
print("\n4. Checking exact hardcoded values:")
# From ultimate_parity_test.py line 79
hardcoded_exact = {
    "tp": 133.84,
    "fp": 552.77,
    "fn": 941.16,
}

print(f"   Hardcoded: {hardcoded_exact}")
print(f"   Real:      tp={alpha_tp:.20f}")
print(f"   Difference: {alpha_tp - hardcoded_exact['tp']:.20f}")

print("\n5. THE ISSUE:")
print("   The get_alpha_metrics() function returns ROUNDED values (133.84, 552.77, 941.16)")
print("   But the actual Alpha values have more precision!")
print("   When Beta calculates exact values and compares to rounded hardcoded values,")
print("   we get small differences like 0.0014!")