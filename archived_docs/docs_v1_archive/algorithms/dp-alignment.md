# Dynamic Programming Alignment Algorithm

## Overview

DP Alignment uses dynamic programming to find the optimal alignment between reference and hypothesis label sequences. It computes edit distance and provides detailed substitution, insertion, and deletion counts.

## Algorithm Description

### Core Concept

DP Alignment treats scoring as a sequence alignment problem:

- **Edit operations**: Insertions, deletions, substitutions
- **Cost matrix**: Dynamic programming table for optimal alignment
- **Backtracking**: Reconstruct aligned sequences
- **NULL sentinels**: Special markers at sequence boundaries

### Key Features

1. **Integer Counts**: All metrics are integers (hits, ins, del, sub)
1. **Substitution Matrix**: Detailed confusion for label substitutions (excludes NULL)
1. **Edit Distance**: Uses standard edit distance as alignment cost
1. **Aligned Output**: Shows exact alignment with gaps

## Implementation Details

### Dynamic Programming Table

The algorithm builds a cost matrix `d[i][j]` where:

- `i` indexes the reference sequence
- `j` indexes the hypothesis sequence
- `d[i][j]` = minimum cost to align ref\[0:i\] with hyp\[0:j\]

```python
# Recurrence relation
d[i][j] = min(
    d[i - 1][j] + penalty_del,  # Delete from ref
    d[i][j - 1] + penalty_ins,  # Insert to hyp
    d[i - 1][j - 1] + penalty_sub,  # Substitute (0 if match)
)
```

### Processing Pipeline

1. **Padding (internal)**:

   - The implementation pads sequences with a `NULL_CLASS` sentinel at the start and end internally. Do not include `"null"` in your input sequences.

1. **Build cost matrix**:

   ```python
   # Initialize borders
   for j in range(1, n):
       d[0][j] = d[0][j - 1] + penalty_ins
   for i in range(1, m):
       d[i][0] = d[i - 1][0] + penalty_del

   # Fill interior
   for j in range(1, n):
       for i in range(1, m):
           # Compute three costs
           del_cost = d[i - 1][j] + penalty_del
           ins_cost = d[i][j - 1] + penalty_ins
           sub_cost = d[i - 1][j - 1]
           if ref[i] != hyp[j]:
               sub_cost += penalty_sub

           # Choose minimum
           d[i][j] = min(del_cost, ins_cost, sub_cost)
   ```

1. **Backtracking**:

   ```python
   # Start from bottom-right
   i, j = m - 1, n - 1
   aligned_ref = []
   aligned_hyp = []

   while i >= 0 or j >= 0:
       if error_type == DELETION:
           aligned_ref.append(ref[i])
           aligned_hyp.append(NULL_CLASS)
           i -= 1
       elif error_type == INSERTION:
           aligned_ref.append(NULL_CLASS)
           aligned_hyp.append(hyp[j])
           j -= 1
       else:  # SUBSTITUTION or MATCH
           aligned_ref.append(ref[i])
           aligned_hyp.append(hyp[j])
           i -= 1
           j -= 1
   ```

## Error Counting

The algorithm maintains multiple counting systems:

### Primary Counts

- **Hits**: Matching labels at aligned positions
- **Insertions**: NULL → label transitions
- **Deletions**: label → NULL transitions
- **Substitutions**: label₁ → label₂ transitions

### NEDC Mappings

- Positive class is `"seiz"`.
- The result exposes `true_positives`, `false_positives`, and `false_negatives` directly:

```python
TP = result.true_positives  # hits for "seiz"
FP = result.false_positives  # insertions of "seiz"
FN = result.false_negatives  # deletions + substitutions from "seiz"
```

## Usage Example

```python
from nedc_bench.algorithms.dp_alignment import DPAligner

# Create aligner with penalties
aligner = DPAligner(penalty_del=1.0, penalty_ins=1.0, penalty_sub=1.0)

# Define label sequences (no NULL sentinels)
ref_sequence = ["seiz", "seiz", "bckg"]
hyp_sequence = ["bckg", "seiz", "seiz"]

# Align sequences
result = aligner.align(ref_sequence, hyp_sequence)

# Access results
print(f"Hits: {result.hits}")
print(f"Total insertions: {result.total_insertions}")
print(f"Total deletions: {result.total_deletions}")
print(f"Total substitutions: {result.total_substitutions}")

# View alignment
for r, h in zip(result.aligned_ref, result.aligned_hyp):
    print(f"{r:10} -> {h:10}")
```

## Substitution Matrix

The algorithm produces a detailed substitution matrix (excluding `NULL_CLASS` transitions, which are counted as insertions/deletions):

```python
substitutions = {
    "seiz": {"bckg": 1},  # "seiz" misclassified as "bckg"
    "bckg": {"seiz": 1},  # "bckg" misclassified as "seiz"
}
```

## Performance Characteristics

- **Time Complexity**: O(m × n) for sequences of length m, n
- **Space Complexity**: O(m × n) for DP table
- **Typical Runtime**: \<100ms for typical sequences

## When to Use DP Alignment

### Recommended for:

- Sequence-level comparison
- Understanding specific error patterns
- Systems where order matters
- Detailed error analysis needed

### Not recommended for:

- Event-based scoring with timing
- Real-time streaming evaluation
- Large sequences (memory intensive)
- Simple hit/miss counting

## Validation

- Parity: Beta matches NEDC v6.0.0 DP alignment exactly on the SSOT parity set. See docs/archive/bugs/FINAL_PARITY_RESULTS.md.

## Related Documentation

- [Algorithm Overview](overview.md) - Comparison of all algorithms
- [Epoch Algorithm](epoch.md) - Alternative sequence scoring
- Source: `nedc_bench/algorithms/dp_alignment.py`
- NEDC Reference: `nedc_eeg_eval_dpalign.py` lines 580–711 (v6.0.0)
