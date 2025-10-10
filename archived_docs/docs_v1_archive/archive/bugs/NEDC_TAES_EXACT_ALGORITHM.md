# NEDC TAES EXACT Algorithm for Perfect Parity

## THE TRUTH: NEDC TAES Multi-Overlap Sequencing

### Core Algorithm Flow

1. **For each reference event:**

   - Find ALL overlapping hypothesis events with same label
   - Call `compute_partial` for each ref-hyp pair

1. **In `compute_partial(ref[i], hyp[j])`:**

   **Case A: hyp.stop >= ref.stop** (Hyp spans beyond ref)

   ```
   ref:     <----->
   hyp:  <---------->  (continues)
   ```

   - Call `ovlp_ref_seqs`:
     - Calculate fractional hit/fa for THIS ref via `calc_hf`
     - miss = 1 - hit for THIS ref
     - **CRITICAL**: For each ADDITIONAL ref that overlaps this same hyp:
       - Add +1.0 to miss (FULL PENALTY!)
       - Mark those refs as processed

   **Case B: ref.stop > hyp.stop** (Ref spans beyond hyp)

   ```
   ref:  <---------->
   hyp:     <----->
   ```

   - Call `ovlp_hyp_seqs`:
     - Calculate fractional hit/fa for THIS hyp via `calc_hf`
     - miss = 1 - hit
     - For each ADDITIONAL hyp that overlaps this same ref:
       - Calculate their fractional hit/fa
       - ADD to total hit
       - SUBTRACT from miss (miss -= ovlp_hit)
       - ADD to fa

### The Key Insight: Why Long Hypotheses Score Poorly

When a hypothesis spans multiple references (common with seizure detection):

```
refs: <--> <--> <--> <--> <-->  (5 separate seizures)
hyp:  <---------------------->  (1 long detection)
```

NEDC scoring:

- First ref: fractional hit (e.g., 0.8), miss = 0.2
- Refs 2-5: Each adds +1.0 to miss!
- Total: hit = 0.8, miss = 0.2 + 4.0 = 4.2
- This is why we see TP=2.66, FN=14.34!

### Exact Implementation Requirements

```python
def score_taes_exact(refs, hyps):
    """EXACT NEDC TAES implementation"""

    # 1. Filter by target label
    refs = [r for r in refs if r.label == "seiz"]
    hyps = [h for h in hyps if h.label == "seiz"]

    # 2. Track processed flags
    ref_flags = [True] * len(refs)
    hyp_flags = [True] * len(hyps)

    total_hit = 0.0
    total_miss = 0.0
    total_fa = 0.0

    # 3. Main loop - process each ref
    for i in range(len(refs)):
        if not ref_flags[i]:
            continue

        # Find overlapping hyps
        for j in range(len(hyps)):
            if not hyp_flags[j]:
                continue

            if not overlaps(refs[i], hyps[j]):
                continue

            # Compute partial scores
            if hyps[j].stop >= refs[i].stop:
                # Hyp extends beyond ref
                hit, miss, fa = ovlp_ref_seqs(refs, hyps, i, j, ref_flags, hyp_flags)
            else:
                # Ref extends beyond hyp
                hit, miss, fa = ovlp_hyp_seqs(refs, hyps, i, j, ref_flags, hyp_flags)

            total_hit += hit
            total_miss += miss
            total_fa += fa

    # 4. Add penalties for unmatched events
    for i, flag in enumerate(ref_flags):
        if flag:  # Unmatched ref
            total_miss += 1.0

    for j, flag in enumerate(hyp_flags):
        if flag:  # Unmatched hyp
            total_fa += 1.0

    return total_hit, total_miss, total_fa


def ovlp_ref_seqs(refs, hyps, r_idx, h_idx, ref_flags, hyp_flags):
    """When hyp spans multiple refs"""

    # Score first ref normally
    hit, fa = calc_hf(refs[r_idx], hyps[h_idx])
    miss = 1.0 - hit

    # Mark as processed
    ref_flags[r_idx] = False
    hyp_flags[h_idx] = False

    # CRITICAL: Check subsequent refs
    for i in range(r_idx + 1, len(refs)):
        if overlaps(refs[i], hyps[h_idx]):
            miss += 1.0  # FULL PENALTY for each additional ref!
            ref_flags[i] = False

    return hit, miss, fa


def ovlp_hyp_seqs(refs, hyps, r_idx, h_idx, ref_flags, hyp_flags):
    """When ref is hit by multiple hyps"""

    # Score first hyp normally
    hit, fa = calc_hf(refs[r_idx], hyps[h_idx])
    miss = 1.0 - hit

    # Mark as processed
    ref_flags[r_idx] = False
    hyp_flags[h_idx] = False

    # Check subsequent hyps
    for j in range(h_idx + 1, len(hyps)):
        if overlaps(refs[r_idx], hyps[j]):
            ovlp_hit, ovlp_fa = calc_hf(refs[r_idx], hyps[j])
            hit += ovlp_hit
            miss -= ovlp_hit  # Reduce miss
            fa += ovlp_fa
            hyp_flags[j] = False

    return hit, miss, fa
```

## Why This Matters for Parity

The current Beta implementation sums fractional hits independently for each ref. This is WRONG!

**Beta (incorrect):**

- Ref 1 overlapped: hit += 0.5, miss += 0.5
- Ref 2 overlapped: hit += 0.5, miss += 0.5
- Total: hit = 1.0, miss = 1.0

**NEDC (correct):**

- Ref 1 overlapped: hit = 0.5, miss = 0.5
- Ref 2 overlapped by SAME hyp: miss += 1.0 (FULL PENALTY)
- Total: hit = 0.5, miss = 1.5

## The Path to Perfect Parity

1. **Implement exact sequencing logic** - Not just calc_hf, but ovlp_ref_seqs and ovlp_hyp_seqs
1. **Process events in order** - NEDC processes refs sequentially, marking flags
1. **Apply correct penalties** - Additional overlapped refs get +1.0 miss each
1. **Handle both directions** - Hyp>ref and ref>hyp have different logic

## Test Case to Verify

```python
# One hyp spanning two refs
refs = [
    Event(0, 10, "seiz"),  # 10 sec
    Event(20, 30, "seiz"),  # 10 sec
]
hyps = [
    Event(5, 25, "seiz"),  # Spans both!
]

# NEDC scoring:
# - First ref: hit = 5/10 = 0.5, miss = 0.5, fa = 10/10 = 1.0
# - Second ref overlapped: miss += 1.0
# Total: TP = 0.5, FN = 1.5, FP = 1.0

# Beta currently would give:
# - First ref: hit = 0.5, miss = 0.5
# - Second ref: hit = 0.5, miss = 0.5
# Total: TP = 1.0, FN = 1.0  (WRONG!)
```

## Conclusion

**YES, PERFECT PARITY IS POSSIBLE!** But it requires implementing NEDC's exact multi-overlap sequencing logic, not just the fractional calc_hf. The key is understanding that NEDC penalizes hypotheses that span multiple references with +1.0 miss for each additional ref, which explains why the scores are so different.
