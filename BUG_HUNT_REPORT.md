# Bug Hunt & Technical Debt Report

**Last Updated**: 2025-10-10  
**Repository**: nedc-bench  
**Branch**: development  
**Reviewer**: AI audit (validated against source on request)

This revision supersedes the earlier draft. Each item below was re-verified in the live repository; findings that could not be reproduced were removed or moved to the “Retired Findings” section.

---

## Executive Summary
- 🔴 **2 P0 issues** confirmed (temp-file leak, unsafe list validation) — address immediately.
- 🟠 **4 P1 issues** (alpha/beta coupling, duplicate augmentation logic, missing parallel error handling, CORS permissiveness).
- 🟡 **3 P2 issues** (timezone-naive timestamps, progress tracker cleanup, silent OpenAPI import failure).
- 🟢 **2 P3 issues** (documentation/observability polish).
- Overall architecture and test coverage remain strong; focus remediation on temp-file lifecycle, orchestrator boundaries, and production hardening.

---

## Review Methodology
- Manual inspection of the API, orchestration, and algorithm modules (≤250 line windows via `sed`).
- Targeted `rg` searches for high-risk patterns (`datetime.utcnow`, `except Exception`, `zip(`).
- Cross-check against FastAPI workflows (upload → queue → worker → metrics).
- Verified previously reported issues; pruned any that did not match the current code.

---

## 🔴 P0 Issues (Production Blockers)

### P0-1: Uploaded files accumulate in `/tmp`
- **Location**: `src/nedc_bench/api/endpoints/evaluation.py:31-58`, `src/nedc_bench/api/services/processor.py:24-83`
- **Details**:
  ```python
  # src/nedc_bench/api/endpoints/evaluation.py:33-36
  ref_path = f"/tmp/{job_id}_ref.csv_bi"
  hyp_path = f"/tmp/{job_id}_hyp.csv_bi"
  ...
  await job_manager.add_job(job)
  ```
  Neither `process_evaluation` nor any other worker tear-down removes the temporary files once a job finishes or fails.
- **Impact**: Long-lived API pods will leak disk space until `/tmp` fills, leading to job failures and potential container eviction.
- **Fix**:
  1. Replace manual paths with `tempfile.NamedTemporaryFile(delete=False)` or a `TemporaryDirectory` per job.
  2. Add cleanup in `process_evaluation` (success + failure paths) and defensive cleanup in `job_manager.shutdown`.
  3. Document retention policy (e.g. keep last N jobs for debugging).

### P0-2: `assert` used for runtime validation in list orchestration
- **Location**: `src/nedc_bench/orchestration/dual_pipeline.py:262-273`
- **Details**:
  ```python
  assert len(ref_files) == len(hyp_files), "List files must have same length"
  for ref_file, hyp_file in zip(ref_files, hyp_files, strict=False):
      ...
  ```
- **Impact**: When Python runs with optimizations (`PYTHONOPTIMIZE=1` or `-O`), the `assert` is stripped, allowing mismatched list lengths to slip through silently; `zip(..., strict=False)` then truncates to the shorter list, dropping evaluations with no warning — a data-integrity failure.
- **Fix**:
  1. Replace `assert` with explicit runtime check (`if len(...) != len(...): raise ValueError(...)`).
  2. Leave `zip` strict mode enabled (`strict=True`) to surface future regressions.
  3. Add unit test covering mismatched list lengths.

---

## 🟠 P1 Issues (High Priority)

### P1-1: Beta pipeline requires Alpha runtime even in beta-only mode
- **Location**: `src/nedc_bench/orchestration/dual_pipeline.py:160-205`, `src/nedc_bench/api/services/async_wrapper.py:30-88`
- **Details**: `DualPipelineOrchestrator` always instantiates `NEDCAlphaWrapper` (`self.alpha_wrapper = NEDCAlphaWrapper(...)`). The async wrapper and parallel evaluator both rely on this orchestrator, so even `pipeline="beta"` requests crash unless the legacy NEDC assets and `NEDC_NFC` env var are present.
- **Impact**: Prevents shipping a pure-beta deployment or running unit tests without the legacy toolchain; increases container size and start-up fragility.
- **Fix**:
  1. Split orchestration so Beta-only execution does not require Alpha (`BetaPipelineOrchestrator`).
  2. Lazily construct the Alpha wrapper only when the request path needs it.
  3. Add smoke tests for `pipeline="beta"` in an environment without `nedc_eeg_eval`.

### P1-2: Background augmentation logic duplicated in three places
- **Location**:
  - `src/nedc_bench/orchestration/dual_pipeline.py:62-95`
  - `src/nedc_bench/algorithms/epoch.py:214-255`
  - `src/nedc_bench/algorithms/ira.py:104-148`
- **Impact**: ~220 lines of near-identical code. Any bug fix or parity tweak must be applied manually in three modules, risking drift and subtle parity mismatches.
- **Fix**:
  1. Extract a shared helper (e.g. `nedc_bench.utils.annotations.fill_background(...)`) with comprehensive tests.
  2. Refactor all call sites to use the helper.
  3. Document the parity rationale once instead of thrice.

### P1-3: Parallel batch evaluation lacks failure isolation
- **Location**: `src/nedc_bench/orchestration/parallel.py:55-77`
- **Details**: Fetched futures are dereferenced with `fut.result()`; any exception aborts the loop and never records which file pair failed.
- **Impact**: One bad file halts the entire batch run with no structured error payload, breaking parity sweeps and CI jobs.
- **Fix**:
  1. Wrap `fut.result()` in `try/except`, log context, and return an error placeholder for that index.
  2. Add integration test where one worker raises.
  3. Propagate aggregated status so callers can retry or surface partial success.

### P1-4: CORS is wide-open in production
- **Location**: `src/nedc_bench/api/main.py:56-63`
- **Details**: `allow_origins=["*"]` with `allow_credentials=True`. Comment notes “configure for production,” but there is no configuration path exposed.
- **Impact**: In production, any origin can make credentialed requests, enabling CSRF and token exfiltration.
- **Fix**:
  1. Drive allowed origins from environment/config (e.g. `CORS_ALLOWED_ORIGINS`).
  2. Default to localhost in dev, enforce strict list elsewhere.
  3. Add documentation in deployment guide and a test covering config parsing.

---

## 🟡 P2 Issues (Medium Priority)

### P2-1: Naive `datetime.utcnow()` usage
- **Location**: `src/nedc_bench/api/endpoints/evaluation.py:47`, `src/nedc_bench/api/services/processor.py:25,61,77`, `src/nedc_bench/api/services/progress_tracker.py:19,29,47`, `src/nedc_bench/api/services/job_manager.py:52`
- **Impact**: Produces naive timestamps (no timezone), complicating serialization and future Python upgrades where `utcnow()` is deprecated.
- **Fix**:
  1. Switch to `datetime.now(timezone.utc)` and ensure JSON responses serialize ISO-8601 with `Z`.
  2. Update tests expecting naive datetimes.

### P2-2: Progress tracker never prunes completed jobs
- **Location**: `src/nedc_bench/api/services/progress_tracker.py:13-60`, `src/nedc_bench/api/services/processor.py:66-83`
- **Impact**: `progress_tracker.progress` retains entries indefinitely; long-running nodes leak memory and stale progress states.
- **Fix**:
  1. Add `ProgressTracker.finish_job(job_id)` to drop state once broadcast completes.
  2. Call cleanup in both success and failure paths.
  3. Add metrics/logging for unexpected lookups.

### P2-3: Silent OpenAPI customization failures
- **Location**: `src/nedc_bench/api/main.py:87-93`
- **Impact**: Any exception when importing `custom_openapi` is swallowed; teams lose documentation without logs.
- **Fix**:
  1. Log at WARN with exception context.
  2. Narrow catch to `ImportError` for the “optional” case.
  3. Add unit test simulating import failure.

---

## 🟢 P3 Issues (Low Priority / Cleanup)

### P3-1: Monitoring package lacks module docstring/export
- **Location**: `src/nedc_bench/monitoring/__init__.py`
- **Fix**: Add brief docstring or export convenience symbols to aid IDE discovery.

### P3-2: Metrics endpoint fallback obscures missing dependency
- **Location**: `src/nedc_bench/api/endpoints/metrics.py:19-53`
- **Impact**: When `prometheus_client` is absent, we return `200 OK` with an empty body; operators may believe metrics are healthy.
- **Fix**: Emit warning log and set status to `503` (or include explanatory payload) when the fallback is active.

---

## Retired Findings (No longer reproducible)
- **Redis health check missing** → `/ready` endpoint already validates Redis (`src/nedc_bench/api/endpoints/health.py:17-27`).
- **WebSocket broadcast leaks disconnected clients** → `broadcast()` collects failures and calls `disconnect()` (`src/nedc_bench/api/services/websocket_manager.py:50-70`).
- **`zip(strict=False)` silently drops pairs** → real issue is the stripped `assert`; addressed as P0-2.
- **“17 silent exception handlers”** → most handlers now log at `debug` or higher; no additional action required beyond targeted improvements above.

---

## Remediation Plan

| Priority | Task | Owner | Target | Notes |
|----------|------|-------|--------|-------|
| P0 | Replace `/tmp` writes with managed temp storage; add cleanup hooks | API team | Sprint +1 | Implement deletion in success/failure paths; add regression test. |
| P0 | Harden list orchestration validation (`strict=True` + explicit error) | Orchestration | Sprint +1 | Cover via unit test and CLI smoke test. |
| P1 | Decouple Beta orchestrator from Alpha dependencies | Orchestration | Sprint +1 | Introduce Beta-only orchestrator and lazy Alpha init. |
| P1 | Extract shared event augmentation helper & refactor call sites | Algorithms | Sprint +2 | Include parity regression tests for each algorithm. |
| P1 | Add per-future error isolation/logging to `ParallelEvaluator` | Orchestration | Sprint +1 | Return partial results with error payloads. |
| P1 | Externalize CORS configuration & document deployment knobs | API team | Sprint +1 | Update docs/k8s manifests and add config validation. |
| P2 | Migrate to timezone-aware timestamps across services | API team | Sprint +2 | Ensure JSON serialization uses ISO-8601 with timezone. |
| P2 | Add progress tracker cleanup when jobs finish | API team | Sprint +1 | Track metrics for active vs. stale progress entries. |
| P2 | Log OpenAPI import failures & narrow exception scope | API team | Sprint +1 | Add unit test for optional docs package missing. |
| P3 | Improve metrics fallback observability | Platform | Backlog | Warn operators when Prometheus exports are disabled. |
| P3 | Add monitoring package docstring/exports | Platform | Backlog | Cosmetic, bundle with documentation sweep. |

---

## Documentation & Testing Updates
- Update deployment docs (`docs/` and `k8s/`) once CORS configuration is parameterized.
- Extend parity test suite to cover the shared augmentation helper.
- Add regression tests for `evaluate_lists` mismatched inputs and temp-file lifecycle (use pytest tmp_path fixtures).
- Document new cleanup behaviour and environment variables in `README.md` / API reference.

---

## Next Steps
1. Land P0 fixes before the next deployment cut; confirm via `make test-fast` and targeted integration tests.
2. Schedule orchestrator refactor and augmentation deduplication in the upcoming sprint (shared helper first, then beta decoupling).
3. After fixes merge, rerun this audit checklist and update the report to reflect resolved items.

This report now reflects the current state of the repository with actionable, prioritized work items. Reach out if you want to break any item into implementation tickets.
