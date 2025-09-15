# Phase 1: Foundation - Containerized Alpha Pipeline
## Vertical Slice Goal: Working Alpha Pipeline with Structured Output

### Duration: 5 Days

### Success Criteria (TDD)
- [ ] Alpha pipeline runs in Docker container
- [ ] Text output parsed to JSON structure
- [ ] All 5 algorithms produce parseable output
- [ ] Golden test file passes with 100% match
- [ ] CI/CD runs Alpha pipeline on every commit

### Day 1: Environment & Container Setup

#### Morning: Docker Environment
```python
# tests/test_alpha_environment.py
import subprocess
def test_docker_build():
    """Alpha container builds successfully"""
    result = subprocess.run(["docker", "build", "-t", "nedc-alpha", "alpha/"])
    assert result.returncode == 0

def test_environment_variables():
    """Container has correct environment"""
    result = subprocess.run(
        ["docker", "run", "nedc-alpha", "env"],
        capture_output=True, text=True
    )
    assert "NEDC_NFC=/opt/nedc" in result.stdout
    # allow extra path segments; check prefix exists
    assert "PYTHONPATH=/opt/nedc/lib" in result.stdout
```

#### Afternoon: Basic Wrapper
```python
# alpha/wrapper/nedc_wrapper.py
import os
import subprocess
from pathlib import Path
from typing import Dict

class NEDCAlphaWrapper:
    def __init__(self):
        self.nedc_root = Path("/opt/nedc")
        os.environ["NEDC_NFC"] = str(self.nedc_root)
        os.environ["PYTHONPATH"] = f"{self.nedc_root}/lib:{os.environ.get('PYTHONPATH', '')}"
        self._validate_installation()

    def _validate_installation(self):
        """TDD: Verify NEDC installation"""
        assert (self.nedc_root / "lib").exists()
        assert (self.nedc_root / "bin" / "nedc_eeg_eval").exists()
```

### Day 2: Output Parser Implementation

#### Morning: Text Parser for TAES
```python
# tests/test_output_parser.py
from alpha.wrapper.parsers import TAESParser
def test_parse_taes_output():
    """Parse TAES text output to structured data"""
    sample_output = """
    NEDC TAES SCORING SUMMARY (v6.0.0):

    Sensitivity (TPR, Recall):      85.0000%
    Specificity (TNR):              92.0000%
    F1 Score (F Ratio):              0.7800
    """
    parser = TAESParser()
    result = parser.parse(sample_output)
    assert result['sensitivity'] == 0.85
    assert result['specificity'] == 0.92
    assert result['f1_score'] == 0.78
```

#### Afternoon: Parser for All Algorithms
```python
# alpha/wrapper/parsers.py
from typing import Dict
class UnifiedOutputParser:
    """Parse all 5 algorithm outputs"""

    def parse_summary(self, text: str) -> Dict:
        return {
            'dp_alignment': self._parse_dp(text),
            'epoch': self._parse_epoch(text),
            'overlap': self._parse_overlap(text),
            'taes': self._parse_taes(text),
            'ira': self._parse_ira(text)
        }
```

#### Wrapper Evaluate Contract
```python
# alpha/wrapper/nedc_wrapper.py (contract)
class NEDCAlphaWrapper:
    def evaluate(self, ref_csv: str, hyp_csv: str) -> Dict:
        """Run nedc_eeg_eval on a single file pair by creating temp lists,
        then parse summary files into structured JSON (all 5 algorithms)."""
        ...
```

### Day 3: Golden Test Implementation

#### Morning: Create Golden Dataset
```python
# tests/golden/test_exact_match.py
from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper
from tests.utils import create_csv_bi_annotation

def test_golden_exact_match():
    """Reference and hypothesis are identical"""
    # Create CSV_BI format test files
    ref_file = create_csv_bi_annotation([
        ("TERM", 0.0, 10.0, "seiz", 1.0),
        ("TERM", 20.0, 30.0, "seiz", 1.0)
    ])
    hyp_file = create_csv_bi_annotation([
        ("TERM", 0.0, 10.0, "seiz", 1.0),
        ("TERM", 20.0, 30.0, "seiz", 1.0)
    ])

    alpha_wrapper = NEDCAlphaWrapper()
    result = alpha_wrapper.evaluate(ref_file, hyp_file)

    # Perfect match should yield 100% for all metrics
    assert result['taes']['sensitivity'] == 1.0
    assert result['taes']['specificity'] == 1.0
    assert result['taes']['f1_score'] == 1.0
```

#### Afternoon: Edge Cases
```python
# tests/golden/test_edge_cases.py
from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper
from tests.utils import create_csv_bi_annotation

def test_no_events_in_reference():
    """Empty reference file - all hypothesis events are false positives"""
    ref_file = create_csv_bi_annotation([])  # No events
    hyp_file = create_csv_bi_annotation([
        ("TERM", 0.0, 10.0, "seiz", 1.0)
    ])

    alpha_wrapper = NEDCAlphaWrapper()
    result = alpha_wrapper.evaluate(ref_file, hyp_file)

    # With no reference events, everything is a false positive
    assert result['taes']['false_positives'] == 1
    assert result['taes']['true_positives'] == 0
    assert result['taes']['sensitivity'] == 0.0  # No true positives possible
```

### Day 4: Integration & CI/CD

#### Morning: Docker Compose Setup
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  alpha:
    build: ./alpha
    volumes:
      - ./tests/data:/data
      - ./output:/output
    environment:
      - NEDC_NFC=/opt/nedc
      - PYTHONPATH=/opt/nedc/lib:/app
```

#### Afternoon: GitHub Actions
```yaml
# .github/workflows/alpha-pipeline.yml
name: Alpha Pipeline Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Alpha Container
        run: docker build -t nedc-alpha alpha/
      - name: Run Golden Tests
        run: |
          docker run -e PYTHONPATH=/opt/nedc/lib:/app -v $PWD/tests:/tests nedc-alpha \
            pytest /tests -q
```

### Day 5: Validation & Documentation

#### Morning: Comprehensive Test Suite
```python
# tests/test_alpha_validation.py
@pytest.mark.parametrize("test_case", load_validation_cases())
def test_alpha_validation_suite(test_case):
    """Run all validation cases from NEDC paper"""
    result = alpha_wrapper.evaluate(
        test_case['ref'],
        test_case['hyp']
    )

    # Allow small numerical tolerance
    for metric, expected in test_case['expected'].items():
        assert abs(result[metric] - expected) < 1e-6
```

#### Afternoon: Documentation
- API documentation for wrapper
- Docker usage guide
- Output format specification

### Deliverables Checklist
- [ ] `alpha/Dockerfile` - Python 3.9+ container with NEDC v6.0.0
- [ ] `alpha/requirements.txt` - numpy==2.0.2, scipy==1.14.1, lxml==5.3.0, tomli==2.0.1, pytest==8.3.2
- [ ] `alpha/wrapper/nedc_wrapper.py` - Python wrapper for subprocess calls
- [ ] `alpha/wrapper/parsers.py` - Text-to-JSON parsers for all 5 algorithms
- [ ] `tests/test_alpha_*.py` - Test suite with golden tests
- [ ] `.github/workflows/alpha-pipeline.yml` - CI/CD pipeline
- [ ] `docs/alpha-pipeline.md` - API and output format documentation

#### Alpha Dockerfile (reference)
```dockerfile
# alpha/Dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

# Vendored NEDC tool and wrapper
COPY nedc_eeg_eval/v6.0.0/ /opt/nedc/
COPY alpha/wrapper/ /app/
COPY alpha/requirements.txt /tmp/requirements.txt

# Python dependencies (include pytest for in-container tests)
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Required env
ENV NEDC_NFC=/opt/nedc
ENV PYTHONPATH=/opt/nedc/lib:/app
WORKDIR /app
```

#### Notes on IRA Output
- IRA does not produce a standalone `summary_ira.txt`; parse the IRA section from `output/summary.txt`.

### Definition of Done
1. ✅ Alpha pipeline runs in Docker
2. ✅ All 5 algorithms produce JSON output
3. ✅ Golden tests pass
4. ✅ CI/CD runs on every commit
5. ✅ Documentation complete

### Next Phase Entry Criteria
- Alpha pipeline stable and tested
- Output format documented
- Ready to implement Beta TAES algorithm

---
## Notes
- Keep wrapper minimal - just parse output
- Don't modify NEDC code at all
- Focus on reproducibility
- Document any quirks found
\n[Archived] Project planning document; final implementation details in docs/.
