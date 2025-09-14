"""Test output parsers for NEDC text format"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.wrapper.parsers import (
    TAESParser,
    DPAlignmentParser,
    EpochParser,
    OverlapParser,
    IRAParser,
    UnifiedOutputParser
)


def test_parse_taes_output():
    """Parse TAES text output to structured data"""
    sample_output = """
    ==============================================================================
    NEDC TAES SCORING SUMMARY (v6.0.0):

                          Targets:          100
                             Hits:           85
                           Misses:           15
                     False Alarms:            8

              True Positives (TP):           85
              True Negatives (TN):           92
             False Positives (FP):            8
             False Negatives (FN):           15

        Sensitivity (TPR, Recall):      85.0000%
                Specificity (TNR):      92.0000%
                  Precision (PPV):      91.3978%
                         Accuracy:      88.5000%
                       F1 Score (F Ratio):       0.8817
    ==============================================================================
    """

    parser = TAESParser()
    result = parser.parse(sample_output)

    assert result['sensitivity'] == 0.85
    assert result['specificity'] == 0.92
    assert abs(result['precision'] - 0.913978) < 1e-6
    assert result['f1_score'] == 0.8817
    assert result['accuracy'] == 0.885
    assert result['true_positives'] == 85
    assert result['false_positives'] == 8


def test_parse_dp_alignment_output():
    """Parse DP Alignment output"""
    sample_output = """
    ==============================================================================
    NEDC DP ALIGNMENT SCORING SUMMARY (v6.0.0):

                          Insertions:            0
                           Deletions:          643

              True Positives (TP):           58
              True Negatives (TN):           88
             False Positives (FP):            0
             False Negatives (FN):          643

        Sensitivity (TPR, Recall):       8.2739%
                Specificity (TNR):     100.0000%
                  Precision (PPV):     100.0000%
                         Accuracy:      18.5044%
                       F1 Score (F Ratio):       0.1528
    ==============================================================================
    """

    parser = DPAlignmentParser()
    result = parser.parse(sample_output)

    assert result['sensitivity'] == 0.082739
    assert result['specificity'] == 1.0
    assert result['precision'] == 1.0
    assert result['f1_score'] == 0.1528
    assert result['insertions'] == 0
    assert result['deletions'] == 643


def test_parse_epoch_output():
    """Parse Epoch-based scoring output"""
    sample_output = """
    ==============================================================================
    NEDC EPOCH SCORING SUMMARY (v6.0.0):

              True Positives (TP):         2804
              True Negatives (TN):         2359
             False Positives (FP):          353
             False Negatives (FN):          600

        Sensitivity (TPR, Recall):      82.3765%
                Specificity (TNR):      86.9885%
                  Precision (PPV):      88.8159%
                         Accuracy:      84.5555%
                       F1 Score (F Ratio):       0.8548
                   Matthews (MCC):       0.6871
    ==============================================================================
    """

    parser = EpochParser()
    result = parser.parse(sample_output)

    assert result['sensitivity'] == 0.823765
    assert result['specificity'] == 0.869885
    assert result['f1_score'] == 0.8548
    assert result['mcc'] == 0.6871


def test_parse_ira_output():
    """Parse Inter-Rater Agreement from main summary"""
    sample_output = """
    ==============================================================================
    NEDC INTER-RATER AGREEMENT SUMMARY (v6.0.0):

    Label: seiz   Kappa:       0.4110
    Label: bckg   Kappa:       0.4110

    SUMMARY:
       Multi-Class Kappa:       0.4110
    ==============================================================================
    """

    parser = IRAParser()
    result = parser.parse(sample_output)

    assert result['kappa'] == 0.4110
    assert 'per_label_kappa' in result and result['per_label_kappa']['seiz'] == 0.4110


def test_unified_parser():
    """Test parsing complete summary with all algorithms"""
    # This would be a full summary.txt content
    sample_summary = """
    ==============================================================================
    File: /output/summary.txt
    Data:
     Ref: ref.list
     Hyp: hyp.list

    ==============================================================================
    NEDC DP ALIGNMENT SCORING SUMMARY (v6.0.0):

        Sensitivity (TPR, Recall):       8.2739%
        F1 Score (F Ratio):       0.1528

    ==============================================================================
    NEDC EPOCH SCORING SUMMARY (v6.0.0):

        Sensitivity (TPR, Recall):      82.3765%
        F1 Score (F Ratio):       0.8548

    ==============================================================================
    NEDC OVERLAP SCORING SUMMARY (v6.0.0):

        Sensitivity (TPR, Recall):      75.0000%
        F1 Score (F Ratio):       0.7500

    ==============================================================================
    NEDC TAES SCORING SUMMARY (v6.0.0):

        Sensitivity (TPR, Recall):      85.0000%
        F1 Score (F Ratio):       0.8817

    ==============================================================================
    NEDC INTER-RATER AGREEMENT SUMMARY (v6.0.0):

    Multi-Class Kappa:                  0.6871
    ==============================================================================
    """

    parser = UnifiedOutputParser()
    results = parser.parse_summary(sample_summary)

    # Check all algorithms were parsed
    assert 'dp_alignment' in results
    assert 'epoch' in results
    assert 'overlap' in results
    assert 'taes' in results
    assert 'ira' in results

    # Spot check some values
    assert results['dp_alignment']['sensitivity'] == 0.082739
    assert results['epoch']['sensitivity'] == 0.823765
    assert results['taes']['sensitivity'] == 0.85
    assert results['ira']['kappa'] == 0.6871
