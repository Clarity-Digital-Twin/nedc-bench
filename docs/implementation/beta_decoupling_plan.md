# Beta/Alpha Decoupling Implementation Plan

## Problem Statement
Beta pipeline cannot run independently because environment setup forces NEDC_NFC even for beta-only requests.

## Root Causes
1. `AsyncOrchestrator.__init__` (async_wrapper.py:27-31) sets NEDC_NFC unconditionally
2. App lifespan (main.py:30-41) sets NEDC_NFC on startup
3. `DualPipelineOrchestrator` has `alpha_wrapper` property (though lazy-loaded)

## Proposed Solution: Router Pattern

### Step 1: Create BetaPipelineOrchestrator
```python
# src/nedc_bench/orchestration/beta_pipeline.py
class BetaPipelineOrchestrator:
    """Pure-beta orchestrator with NO Alpha dependencies"""

    def __init__(self):
        self.beta = BetaPipeline()  # No alpha_wrapper property

    def evaluate(self, ref_file: str, hyp_file: str, algorithm: str) -> Any:
        """Run beta-only evaluation"""
        if algorithm == "taes":
            return self.beta.evaluate_taes(Path(ref_file), Path(hyp_file))
        elif algorithm == "dp":
            return self.beta.evaluate_dp(Path(ref_file), Path(hyp_file))
        # ... etc
```

### Step 2: Create OrchestatorRouter
```python
# src/nedc_bench/orchestration/router.py
class OrchestratorRouter:
    """Route to correct orchestrator based on pipeline type"""

    def __init__(self):
        self._dual_orch = None
        self.beta_orch = BetaPipelineOrchestrator()

    @property
    def dual_orch(self) -> DualPipelineOrchestrator:
        """Lazy-load dual orchestrator (requires NEDC_NFC)"""
        if self._dual_orch is None:
            if "NEDC_NFC" not in os.environ:
                raise RuntimeError(
                    "NEDC_NFC required for dual/alpha pipelines. "
                    "Use pipeline='beta' for NEDC-independent execution."
                )
            self._dual_orch = DualPipelineOrchestrator()
        return self._dual_orch

    def get_orchestrator(self, pipeline: str):
        if pipeline in {"beta"}:
            return self.beta_orch
        elif pipeline in {"dual", "alpha"}:
            return self.dual_orch
        raise ValueError(f"Unknown pipeline: {pipeline}")
```

### Step 3: Update AsyncOrchestrator
```python
# src/nedc_bench/api/services/async_wrapper.py
class AsyncOrchestrator:
    def __init__(self, max_workers: int = 4):
        # REMOVE forced NEDC_NFC setup
        self.router = OrchestratorRouter()  # Smart router
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def evaluate(self, ref_file: str, hyp_file: str,
                      algorithm: str, pipeline: str) -> dict:
        orch = self.router.get_orchestrator(pipeline)
        # Route to correct orchestrator...
```

### Step 4: Update App Lifespan
```python
# src/nedc_bench/api/main.py
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # REMOVE forced NEDC_NFC setup for beta-only deployments
    # Only validate NEDC_NFC if dual/alpha pipeline used
    logger.info("Starting NEDC-BENCH API (beta-capable)")
    # ...
```

### Step 5: Add Beta-Only Integration Test
```python
# tests/api/test_beta_independent.py
@pytest.mark.skipif(
    Path("nedc_eeg_eval/v6.0.0").exists(),
    reason="Test requires NEDC directory to be absent"
)
def test_beta_runs_without_nedc_directory():
    """Verify Beta can run without legacy assets"""
    # Unset NEDC_NFC
    os.environ.pop("NEDC_NFC", None)

    # Create beta orchestrator
    orch = BetaPipelineOrchestrator()

    # Should work without NEDC
    result = orch.evaluate(ref_file, hyp_file, "taes")
    assert result is not None
```

## Benefits
1. ✅ Beta can run in lightweight containers (no 1GB legacy assets)
2. ✅ Beta tests don't require NEDC directory
3. ✅ Clear separation of concerns
4. ✅ Dual/Alpha still work exactly as before (backward compatible)

## Migration Path
- **Phase 1**: Implement router pattern (1-2 hours)
- **Phase 2**: Update async_wrapper to use router (30 min)
- **Phase 3**: Remove forced NEDC_NFC from startup (15 min)
- **Phase 4**: Add integration tests (1 hour)
- **Phase 5**: Update deployment docs (30 min)

**Total Effort**: ~4 hours

## Backward Compatibility
- ✅ Existing dual/alpha requests work identically
- ✅ No breaking changes to API endpoints
- ✅ Only internal orchestration routing changes
