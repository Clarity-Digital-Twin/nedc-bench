#!/usr/bin/env python3
"""Test that duration is properly read and aggregated"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nedc_bench.models.annotations import AnnotationFile

# Test single file duration reading
test_file = Path("data/csv_bi_parity/csv_bi_export_clean/ref") / "aaaaaajy_s001_t000.csv_bi"

if test_file.exists():
    ann = AnnotationFile.from_csv_bi(test_file)
    print(f"File: {test_file.name}")
    print(f"Duration from metadata: {ann.duration} seconds")

    # What Beta was doing wrong
    if ann.events:
        wrong_duration = max(e.stop_time for e in ann.events)
        print(f"Wrong duration (max stop): {wrong_duration} seconds")

        # Correct event span
        event_span = max(e.stop_time for e in ann.events) - min(e.start_time for e in ann.events)
        print(f"Event span: {event_span} seconds")

    print(f"\nCorrect duration to use: {ann.duration} (from metadata)")

    # Now test aggregation
    print("\n" + "="*50)
    print("Testing aggregation across multiple files...")

    ref_dir = Path("data/csv_bi_parity/csv_bi_export_clean/ref")
    files = list(ref_dir.glob("*.csv_bi"))[:10]  # Test first 10

    total_duration = 0.0
    for f in files:
        ann = AnnotationFile.from_csv_bi(f)
        total_duration += ann.duration
        print(f"{f.name}: {ann.duration:.2f} seconds")

    print(f"\nTotal duration (CORRECT): {total_duration:.2f} seconds")
    print(f"Average per file: {total_duration/len(files):.2f} seconds")
else:
    print(f"Test file not found: {test_file}")