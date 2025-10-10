# Archive Documentation Migration Plan

This plan inventories the content that still lives under `docs/archive/` and
documents where each topic should land inside the active documentation tree.
Nothing in the archive has been deleted yet—this is the roadmap we will follow
before removing the archived copies.

## Status & Parity Reports

| Archive File | Primary Content | Proposed Destination | Notes |
| --- | --- | --- | --- |
| `docs/archive/status/CURRENT_STATUS.md` | Snapshot of algorithm parity metrics (all five algorithms) | Create `docs/reference/parity.md` | Fold the tables and verification commands into a living parity status page. |
| `docs/archive/status/AI_AGENT_REVIEW_FINAL.md` | Detailed review of AI-driven fixes | `docs/developer/debugging.md` (new section) | Summarise key lessons learned in the debugging guide; link to parity page for metrics. |
| `docs/archive/status/DOCUMENTATION_STRUCTURE.md` | Outline of existing doc set | `docs/README.md` (appendix) | Use relevant points to tighten the main docs overview; retire redundant parts. |
| `docs/archive/status/DOD_CHECKLIST.md` & `DOD_COMPLETION_REPORT.md` | Definition of done checklist and completion evidence | `docs/developer/contributing.md` (quality checklist section) | Extract actionable acceptance criteria, reference in PR guidance. |
| `docs/archive/status/OUTDATED_DOCS_INDEX.md` | Truthiness tracker for docs | `docs/README.md` (maintenance section) | Translate into guidance on how to verify freshness; link to new parity page. |

## Bug Investigations & Fix Write-ups

| Archive File | Primary Content | Proposed Destination | Notes |
| --- | --- | --- | --- |
| `docs/archive/bugs/FINAL_PARITY_RESULTS.md` | Final parity tables and metric comparisons | `docs/reference/parity.md` | Use as historical data; include condensed tables and link to parity tests. |
| `docs/archive/bugs/PARITY_TESTING_SSOT.md` | Testing methodology and scripts | `docs/TESTING.md` | Integrate procedural guidance and CLI snippets under integration tests. |
| `docs/archive/bugs/CRITICAL_BUGS_ALL_ALGORITHMS.md` & related per-algorithm fixes (`EPOCH_BUG_FIXED.md`, `ALPHA_WRAPPER_P0_BUG.md`, etc.) | Root-cause analyses and fixes | Individual algorithm pages (`docs/algorithms/*.md`) | Add “History & Fixes” call-outs describing previous bugs and resolutions. |
| `docs/archive/bugs/BUG_2_EPOCH_DEEP_ANALYSIS.md`, `EPOCH_PARITY_INVESTIGATION.md`, `P0_CRITICAL_BUG_DURATION.md` | Deep dives on epoch/TAES defects | `docs/algorithms/epoch.md` and `docs/algorithms/taes.md` | Summarise lessons learned; add references to unit tests ensuring regressions stay fixed. |
| `docs/archive/bugs/IRA_KAPPA_FIX.md`, `TAES_INVESTIGATION.md` | Specific algorithm nuances | `docs/algorithms/ira.md`, `docs/algorithms/taes.md` | Incorporate nuance and precision tolerances into algorithm reference sections. |
| `docs/archive/bugs/NEDC_TAES_EXACT_ALGORITHM.md`, `NEDC_EEG_EVAL_ANALYSIS.md` | Comparisons against legacy implementation | `docs/reference/faq.md` or new “Legacy Parity” subsection | Provide authoritative answers for parity questions. |

## Build & Implementation Plans

| Archive File | Primary Content | Proposed Destination | Notes |
| --- | --- | --- | --- |
| `docs/archive/bulid_implementation/ARCHITECTURE_PROPOSAL.md`, `ARCHITECTURE_COMPARISON.md` | Clean architecture direction | `docs/developer/architecture.md` | Merge relevant diagrams and phased roadmap; remove duplicate wording. |
| `docs/archive/bulid_implementation/PHASE_1_FOUNDATION.md` ... `PHASE_5_PRODUCTION.md` | Phased migration plan and deliverables | `docs/implementation/` | Convert into a single “refactor roadmap” page or appendices within existing implementation docs. |
| `docs/archive/bulid_implementation/REFACTOR_RISK_ANALYSIS.md`, `REFACTOR_COMPLETION_REPORT.md` | Risk assessment and completion proof | `docs/developer/architecture.md` (appendix) | Distil risk considerations and link to completion evidence. |

## Technical Research

| Archive File | Primary Content | Proposed Destination | Notes |
| --- | --- | --- | --- |
| `docs/archive/technical/SZCORE_ANALYSIS.md` | Competitive analysis of SzCORE platform | `docs/developer/benchmarking.md` | Add a “Market Research” section highlighting takeaways for NEDC-BENCH. |

## Execution Checklist

1. Draft `docs/reference/parity.md` with consolidated metrics, verification commands, and links to automated tests.
2. Update algorithm reference pages with “Troubleshooting & History” subsections that capture the resolved bug insights.
3. Refresh developer guides (`architecture.md`, `debugging.md`, `contributing.md`, `benchmarking.md`) using the mapped content.
4. Once each section is migrated, add traceable notes (e.g., in PR descriptions or doc front matter) pointing back to the archive before final deletion.

This mapping keeps archive files untouched for now while giving us a clear, testable migration path toward a self-contained `docs/` directory.
