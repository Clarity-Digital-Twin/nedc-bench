# Phase 4: API Layer - REST API with Dual Pipeline Orchestration
## Vertical Slice Goal: Production API with Real-time Dual Validation

### Duration: 5 Days

### Success Criteria (TDD)
- [ ] FastAPI REST endpoints operational
- [ ] Dual pipeline orchestration working
- [ ] WebSocket for real-time updates
- [ ] API fully documented (OpenAPI)
- [ ] Load testing passes (100 req/sec)

### Day 1: FastAPI Foundation

#### Morning: Basic API Structure
```python
# tests/test_api_basic.py
from fastapi.testclient import TestClient

def test_api_health_check():
    """API health endpoint works"""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "alpha_pipeline" in response.json()
    assert "beta_pipeline" in response.json()
```

#### Afternoon: Core Endpoints
```python
# api/main.py
from fastapi import FastAPI, UploadFile, HTTPException
from typing import List, Optional
import uuid

app = FastAPI(
    title="NEDC-BENCH API",
    version="1.0.0",
    description="Dual-pipeline EEG evaluation benchmarking"
)

@app.post("/evaluate/", response_model=EvaluationResponse)
async def evaluate(
    reference: UploadFile,
    hypothesis: UploadFile,
    algorithms: List[str] = ["all"],
    pipeline: str = "dual"  # "alpha", "beta", or "dual"
) -> EvaluationResponse:
    """Submit evaluation job"""

    # Validate files
    if not reference.filename.endswith('.csv_bi'):
        raise HTTPException(400, "Reference must be CSV_BI format")

    # Create job
    job_id = str(uuid.uuid4())
    job = EvaluationJob(
        id=job_id,
        reference=await reference.read(),
        hypothesis=await hypothesis.read(),
        algorithms=algorithms,
        pipeline=pipeline
    )

    # Queue for processing
    await job_queue.put(job)

    return EvaluationResponse(
        job_id=job_id,
        status="queued",
        message="Evaluation job submitted"
    )
```

### Day 2: Dual Pipeline Orchestration

#### Morning: Async Orchestrator
```python
# tests/test_orchestration.py
@pytest.mark.asyncio
async def test_dual_pipeline_orchestration():
    """Test dual pipeline runs in parallel"""
    orchestrator = DualPipelineOrchestrator()

    start = time.time()
    result = await orchestrator.evaluate(
        ref_data=sample_ref,
        hyp_data=sample_hyp,
        algorithms=["taes"]
    )
    duration = time.time() - start

    # Should run in parallel, not sequential
    assert duration < (alpha_time + beta_time) * 0.8
    assert result.alpha_result is not None
    assert result.beta_result is not None
    assert result.parity_report is not None
```

#### Afternoon: Result Aggregation
```python
# api/orchestrator.py
import asyncio
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DualPipelineResult:
    job_id: str
    alpha_result: Dict
    beta_result: Dict
    parity_report: ParityReport
    execution_time: float
    selected_result: Dict  # Beta if parity passes, else Alpha

class DualPipelineOrchestrator:
    def __init__(self):
        self.alpha = AlphaPipeline()
        self.beta = BetaPipeline()
        self.validator = ParityValidator()

    async def evaluate(self,
                       ref_data: bytes,
                       hyp_data: bytes,
                       algorithms: List[str]) -> DualPipelineResult:
        """Run dual pipeline evaluation"""

        start_time = time.time()

        # Run both pipelines in parallel
        alpha_task = asyncio.create_task(
            self.alpha.evaluate_async(ref_data, hyp_data, algorithms)
        )
        beta_task = asyncio.create_task(
            self.beta.evaluate_async(ref_data, hyp_data, algorithms)
        )

        # Wait for both
        alpha_result, beta_result = await asyncio.gather(
            alpha_task, beta_task
        )

        # Validate parity
        parity = self.validator.compare(alpha_result, beta_result)

        # Select result (Beta if parity, else Alpha as ground truth)
        selected = beta_result if parity.passed else alpha_result

        return DualPipelineResult(
            job_id=str(uuid.uuid4()),
            alpha_result=alpha_result,
            beta_result=beta_result,
            parity_report=parity,
            execution_time=time.time() - start_time,
            selected_result=selected
        )
```

### Day 3: WebSocket & Real-time Updates

#### Morning: WebSocket Implementation
```python
# tests/test_websocket.py
@pytest.mark.asyncio
async def test_websocket_progress():
    """Test real-time progress updates"""
    async with websocket_connect("/ws/test-job-id") as ws:
        # Submit job
        job_id = submit_evaluation_job()

        # Should receive progress updates
        message = await ws.receive_json()
        assert message["type"] == "progress"
        assert message["stage"] == "alpha_pipeline"

        message = await ws.receive_json()
        assert message["type"] == "progress"
        assert message["stage"] == "beta_pipeline"

        message = await ws.receive_json()
        assert message["type"] == "complete"
        assert "results" in message
```

#### Afternoon: Progress Tracking
```python
# api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    async def broadcast_progress(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass  # Connection closed

manager = ConnectionManager()

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
```

### Day 4: Error Handling & Validation

#### Morning: Input Validation
```python
# tests/test_api_validation.py
def test_invalid_file_format():
    """API rejects invalid file formats"""
    client = TestClient(app)

    # Wrong format
    response = client.post(
        "/evaluate/",
        files={
            "reference": ("ref.txt", b"invalid", "text/plain"),
            "hypothesis": ("hyp.txt", b"invalid", "text/plain")
        }
    )

    assert response.status_code == 400
    assert "CSV_BI format" in response.json()["detail"]
```

#### Afternoon: Error Recovery
```python
# api/error_handling.py
from fastapi import HTTPException
from typing import Optional
import traceback

class EvaluationError(Exception):
    """Base exception for evaluation errors"""
    pass

class PipelineError(EvaluationError):
    """Pipeline execution error"""
    pass

class ParityError(EvaluationError):
    """Parity validation failed"""
    pass

@app.exception_handler(EvaluationError)
async def evaluation_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc() if DEBUG else None
        }
    )

async def safe_evaluate(job: EvaluationJob) -> Dict:
    """Evaluate with error handling"""
    try:
        result = await orchestrator.evaluate(
            job.reference,
            job.hypothesis,
            job.algorithms
        )

        if not result.parity_report.passed:
            # Log parity failure but don't fail job
            logger.warning(f"Parity failed for job {job.id}")
            await notify_parity_failure(job.id, result.parity_report)

        return result.selected_result

    except Exception as e:
        logger.error(f"Evaluation failed for job {job.id}: {e}")
        raise EvaluationError(f"Evaluation failed: {str(e)}")
```

### Day 5: Documentation & Load Testing

#### Morning: OpenAPI Documentation
```python
# api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class EvaluationRequest(BaseModel):
    """Request model for evaluation"""
    algorithms: List[str] = Field(
        default=["all"],
        description="Algorithms to run: dp, epoch, overlap, taes, ira, or all"
    )
    pipeline: str = Field(
        default="dual",
        description="Pipeline to use: alpha, beta, or dual"
    )

    class Config:
        schema_extra = {
            "example": {
                "algorithms": ["taes", "epoch"],
                "pipeline": "dual"
            }
        }

class EvaluationResponse(BaseModel):
    """Response model for evaluation"""
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Job status: queued, processing, complete, failed")
    results: Optional[Dict] = Field(description="Evaluation results when complete")
    parity_passed: Optional[bool] = Field(description="Whether dual pipelines matched")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with examples"""
    ...
```

#### Afternoon: Load Testing
```python
# tests/test_load.py
import asyncio
import aiohttp
import time

async def single_request(session, ref, hyp):
    """Single evaluation request"""
    async with session.post(
        "http://localhost:8000/evaluate/",
        data={"reference": ref, "hypothesis": hyp}
    ) as response:
        return await response.json()

async def load_test(n_requests: int = 100):
    """Load test with concurrent requests"""
    ref = load_test_file("ref.csv_bi")
    hyp = load_test_file("hyp.csv_bi")

    async with aiohttp.ClientSession() as session:
        start = time.time()

        tasks = [
            single_request(session, ref, hyp)
            for _ in range(n_requests)
        ]

        results = await asyncio.gather(*tasks)

        duration = time.time() - start
        rps = n_requests / duration

        assert rps >= 100, f"Only {rps:.1f} req/sec, need 100+"
        assert all(r["status"] in ["queued", "processing"] for r in results)
```

### Deliverables Checklist
- [ ] `api/main.py` - FastAPI application
- [ ] `api/orchestrator.py` - Dual pipeline orchestration
- [ ] `api/websocket.py` - WebSocket support
- [ ] `api/schemas.py` - Pydantic models
- [ ] `api/error_handling.py` - Error handling
- [ ] `tests/test_api_*.py` - API tests
- [ ] `tests/test_load.py` - Load testing
- [ ] `docs/api/` - API documentation

### Definition of Done
1. ✅ REST API operational
2. ✅ Dual pipeline orchestration working
3. ✅ WebSocket real-time updates
4. ✅ 100+ requests/second supported
5. ✅ Full OpenAPI documentation

### Next Phase Entry Criteria
- API fully functional
- Load testing passed
- Ready for production deployment

---
## Notes
- Use FastAPI for automatic OpenAPI generation
- Keep endpoints simple and RESTful
- Implement proper error handling
- Consider rate limiting for production
- Document all endpoints thoroughly