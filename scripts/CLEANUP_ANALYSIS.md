# Scripts Cleanup Analysis

## Current Scripts Assessment

### 🟢 KEEP - Core Operational Scripts

1. **ultimate_parity_test.py** - Main parity validation script
   - Purpose: Comprehensive test of all 5 algorithms Alpha vs Beta
   - Status: Essential for validation
   - Action: Keep and polish

2. **run_alpha_complete.py** - Run full Alpha pipeline
   - Purpose: Execute NEDC v6.0.0 on all test data
   - Status: Essential for Alpha pipeline
   - Action: Keep

3. **run_beta_batch.py** - Run all Beta algorithms
   - Purpose: Execute our implementation on all test data
   - Status: Essential for Beta pipeline
   - Action: Keep

4. **compare_parity.py** - Compare Alpha vs Beta results
   - Purpose: Simple comparison of SSOT JSON files
   - Status: Useful for quick checks
   - Action: Keep but simplify

5. **parse_alpha_results.py** - Parse NEDC output to JSON
   - Purpose: Convert NEDC text output to structured JSON
   - Status: Essential for pipeline
   - Action: Keep

### 🔴 DELETE - Debug/Investigation Scripts (No longer needed)

1. **debug_ira_difference.py** - IRA debugging
   - Purpose: Debug IRA differences (now fixed)
   - Action: DELETE

2. **debug_parity_calculation.py** - Debug rounding issue
   - Purpose: Found the rounding bug in test script
   - Action: DELETE

3. **debug_taes_exact.py** - Debug TAES values
   - Purpose: Investigated TAES differences (was test bug)
   - Action: DELETE

4. **localize_epoch_mismatches.py** - Debug epoch scoring
   - Purpose: Found epoch differences (now fixed)
   - Action: DELETE

5. **test_epoch_augmentation.py** - Test augmentation fix
   - Purpose: Tested the fix for epoch gap filling
   - Action: DELETE

6. **test_ira_with_augmentation.py** - Test IRA with augmentation
   - Purpose: Validated IRA fix
   - Action: DELETE

### 🟡 MERGE/REFACTOR - List Creation Scripts

1. **create_correct_lists.py** - Create proper list files
   - Purpose: Generate list files with correct paths
   - Action: MERGE into single utility script

2. **create_runtime_lists.py** - Create runtime list files
   - Purpose: Similar to above
   - Action: MERGE with create_correct_lists.py

3. **test_parity_subset.py** - Test on subset of files
   - Purpose: Quick testing on small dataset
   - Action: REFACTOR into ultimate_parity_test.py with --subset flag

### 🔵 MISSING - Should Add

1. **run_single_file.py** - Process single file pair
   - Purpose: Debug/test individual files
   - Action: CREATE

2. **benchmark.py** - Performance benchmarking
   - Purpose: Measure speed Alpha vs Beta
   - Action: CREATE (optional)

## Proposed New Structure

```
scripts/
├── README.md                    # Clear documentation
├── core/                        # Essential operational scripts
│   ├── run_alpha.py            # Run Alpha pipeline
│   ├── run_beta.py             # Run Beta pipeline
│   ├── validate_parity.py      # Main parity validation
│   └── parse_nedc_output.py    # Parse NEDC text to JSON
├── utils/                       # Utility scripts
│   ├── create_lists.py         # Generate list files for testing
│   └── process_single.py       # Process single file pair
└── benchmarks/                  # Performance scripts (optional)
    └── benchmark_pipelines.py   # Speed comparisons
```

## Cleanup Actions

1. Delete all debug_*.py scripts
2. Delete test_*_augmentation.py scripts
3. Merge list creation scripts
4. Rename and reorganize remaining scripts
5. Add proper docstrings and argument parsing
6. Update README.md with clear usage examples