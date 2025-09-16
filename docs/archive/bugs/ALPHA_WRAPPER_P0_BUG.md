# 🚨 P0 CRITICAL BUG: ALPHA WRAPPER BROKEN 🚨

## NEDC v6.0.0 Cannot Be Run - This Blocks ALL Parity Testing!

**Created:** September 15, 2025
**Severity:** P0 - CRITICAL BLOCKER
**Status:** ✅ FIXED!

## THE PROBLEM

Our Alpha wrapper (NEDC v6.0.0) is COMPLETELY BROKEN. This is fucking weird because:

1. It's just Python code wrapping Python code
1. It worked before in tests
1. The vendored NEDC tool is unchanged
1. But now it can't even find files that clearly exist!

## SYMPTOMS

### Attempt 1: Direct Python execution

```bash
python nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval \
    data/csv_bi_parity/csv_bi_export_clean/ref_runtime.list \
    data/csv_bi_parity/csv_bi_export_clean/hyp_runtime.list
```

**Error:** `ModuleNotFoundError: No module named 'nedc_cmdl_parser'`

### Attempt 2: With environment variables

```bash
export NEDC_NFC=/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/nedc-bench/nedc_eeg_eval/v6.0.0
export PYTHONPATH=$NEDC_NFC/lib:$PYTHONPATH
python $NEDC_NFC/bin/nedc_eeg_eval [lists]
```

**Error:**

```
Error: nedc_file_tools.py (line: 656) get_flist: file not found (data/csv_bi_parity/csv_bi_export_clean/ref_runtime.list)
```

### Attempt 3: Using run_nedc.sh wrapper

```bash
./run_nedc.sh data/csv_bi_parity/csv_bi_export_clean/ref_runtime.list \
              data/csv_bi_parity/csv_bi_export_clean/hyp_runtime.list
```

**Error:** Same file not found error

## WHAT WE KNOW

1. **Files DO exist:**

```bash
$ ls -la data/csv_bi_parity/csv_bi_export_clean/*.list
-rwxrwxrwx 1 jj jj 229000 hyp_runtime.list
-rwxrwxrwx 1 jj jj 229000 ref_runtime.list
```

2. **Original NEDC demo lists use $NEDC_NFC:**

```
$NEDC_NFC/data/csv/ref/aaaaaasf_s001_t000.csv_bi
```

3. **Our lists use absolute paths:**

```
/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/nedc-bench/data/csv_bi_parity/csv_bi_export_clean/ref/aaaaaajy_s001_t000.csv_bi
```

## INVESTIGATION CHECKLIST

- [ ] Check if NEDC needs to be run from its own directory
- [ ] Test with relative paths instead of absolute
- [ ] Check if $NEDC_NFC substitution is working
- [ ] Verify nedc_cmdl_parser module location
- [ ] Test with original NEDC demo data to confirm tool works at all
- [ ] Check Python path resolution in NEDC code
- [ ] Look at nedc_file_tools.py line 656 to see why it fails

## CODE TO INVESTIGATE

### nedc_file_tools.py line 656

Need to check what `get_flist` is doing and why it can't find files that exist.

### NEDCAlphaWrapper class

Location: `nedc_bench/alpha/wrapper/nedc_wrapper.py`
This is our wrapper - is it broken?

### run_nedc.sh

Location: Project root
This shell wrapper - what's it actually doing?

## ROOT CAUSE FOUND! 🔍

The `run_nedc.sh` script:

1. Changes directory to `nedc_eeg_eval/v6.0.0/`
1. THEN tries to find the list files

This means:

- List file paths given to run_nedc.sh need to be relative to PROJECT ROOT
- But CONTENTS of list files need paths relative to NEDC directory!

Example:

```bash
# From project root:
./run_nedc.sh data/lists/ref.list data/lists/hyp.list

# run_nedc.sh does: cd nedc_eeg_eval/v6.0.0
# Now it looks for: data/lists/ref.list FROM THAT DIRECTORY
# Which would be: nedc_eeg_eval/v6.0.0/data/lists/ref.list
```

## IMMEDIATE ACTIONS NEEDED

1. **Test with original demo data** - Does NEDC work AT ALL?
1. **Debug path resolution** - Add logging to see what paths it's actually looking for
1. **Try different path formats** - Relative, absolute, with $NEDC_NFC
1. **Check working directory** - Maybe it needs to run from nedc_eeg_eval/v6.0.0/

## WHY THIS IS P0 CRITICAL

Without Alpha working:

- ❌ Cannot verify parity
- ❌ Cannot get true NEDC baseline
- ❌ Cannot validate our implementation
- ❌ Entire dual-pipeline architecture is broken
- ❌ We're flying blind with only Beta results

## THE WEIRD PART

This WORKED in our tests before! Check:

- `tests/test_nedc_wrapper.py` - These tests passed!
- `tests/test_dual_pipeline.py` - This used Alpha wrapper!

Something changed or our test data was different.

## THE FIX 🎉

The solution is simple but non-obvious:

1. **List files must be placed relative to where run_nedc.sh WILL LOOK**

   - run_nedc.sh changes to `nedc_eeg_eval/v6.0.0/`
   - So list files must be findable from THAT directory

1. **Contents of list files must have paths relative to NEDC directory**

   - Use `../../data/csv_bi_parity/...` to go back up from NEDC dir

1. **Working example:**

```bash
# Create lists in NEDC directory
mkdir -p nedc_eeg_eval/v6.0.0/test_lists

# Contents use relative paths FROM NEDC dir
echo '../../data/csv_bi_parity/csv_bi_export_clean/ref/file.csv_bi' > nedc_eeg_eval/v6.0.0/test_lists/ref.list

# Run with paths relative to project root
./run_nedc.sh test_lists/ref.list test_lists/hyp.list
```

## LESSON LEARNED

The Alpha wrapper was NEVER broken! It was just a confusing path resolution issue because:

- run_nedc.sh changes directory before running
- Paths are resolved from different directories at different times
- Error messages were misleading

**Status:** ✅ FIXED AND WORKING!
