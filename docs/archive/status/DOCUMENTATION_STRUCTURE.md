# NEDC-BENCH Documentation Structure

## Canonical Documentation Plan

This document outlines the complete documentation structure for NEDC-BENCH. Each document will be created with accurate, up-to-date information extracted from the codebase and relevant archived documentation.

### 📚 Documentation Categories

#### 1. Getting Started

- **README.md** - Project overview and badges ✅ (exists, needs review)
- **installation.md** - Installation instructions for all platforms
- **quickstart.md** - 5-minute guide to first evaluation

#### 2. User Guide

- **user-guide/overview.md** - What NEDC-BENCH does and why
- **user-guide/algorithms.md** - Explanation of 5 algorithms (TAES, Epoch, Overlap, DP, IRA)
- **user-guide/input-formats.md** - CSV_BI and XML annotation formats
- **user-guide/output-formats.md** - Understanding evaluation results
- **user-guide/cli-usage.md** - Command-line interface guide
- **user-guide/api-usage.md** - REST API usage guide

#### 3. API Documentation

- **api/openapi.md** - OpenAPI/Swagger specification
- **api/endpoints.md** - All REST endpoints with examples
- **api/websocket.md** - Real-time WebSocket interface
- **api/python-client.md** - Python client SDK usage
- **api/examples.md** - Complete code examples

#### 4. Developer Guide

- **developer/architecture.md** - Dual-pipeline architecture explanation
- **developer/contributing.md** - How to contribute to the project
- **developer/testing.md** - Running and writing tests
- **developer/code-style.md** - Code standards and linting
- **developer/debugging.md** - Debugging tips and tools
- **developer/benchmarking.md** - Performance testing

#### 5. Algorithm Reference

- **algorithms/overview.md** - Algorithm comparison table
- **algorithms/taes.md** - Time-Aligned Event Scoring
- **algorithms/epoch.md** - Epoch-based scoring
- **algorithms/overlap.md** - Overlap detection
- **algorithms/dp-alignment.md** - Dynamic Programming alignment
- **algorithms/ira.md** - Inter-Rater Agreement (Cohen's kappa)
- **algorithms/metrics.md** - FA/24h and other metrics

#### 6. Deployment

- **deployment.md** - Overview ✅ (exists, needs update)
- **deployment/docker.md** - Docker deployment guide
- **deployment/kubernetes.md** - K8s deployment with Helm
- **deployment/configuration.md** - Environment variables and config
- **deployment/monitoring.md** - Prometheus metrics and alerts
- **deployment/scaling.md** - Horizontal scaling guide
- **deployment/troubleshooting.md** - Common issues and solutions

#### 7. Reference

- **reference/configuration.md** - All configuration options
- **reference/cli.md** - Complete CLI reference
- **reference/api.md** - API reference (auto-generated)
- **reference/glossary.md** - EEG and algorithm terminology
- **reference/faq.md** - Frequently asked questions
- **reference/changelog.md** - Version history

#### 8. Migration

- **migration/from-nedc.md** - Migrating from original NEDC v6.0.0
- **migration/upgrade-guide.md** - Upgrading NEDC-BENCH versions
- **migration/data-formats.md** - Converting between formats

### 📝 Information Sources

Each document will be populated from:

1. **Codebase Analysis**:

   - API endpoints from `nedc_bench/api/`
   - Algorithm implementations from `nedc_bench/algorithms/`
   - Configuration from `pyproject.toml`, `docker-compose.yml`
   - Scripts from `scripts/` directory
   - Tests from `tests/` for examples

1. **Archived Documentation** (when relevant):

   - Algorithm details from `NEDC_TAES_EXACT_ALGORITHM.md`
   - Architecture from `NEDC_BENCH_IMPLEMENTATION_PLAN.md`
   - Parity results from `FINAL_PARITY_RESULTS.md`
   - Bug fixes from various bug reports

1. **Generated Content**:

   - API docs from FastAPI's automatic OpenAPI generation
   - CLI help from argparse/click documentation
   - Test coverage reports

### 🎯 Documentation Standards

Each document should:

- Start with a clear purpose statement
- Include practical examples
- Reference relevant code files with `path:line` format
- Link to related documents
- Include last-updated timestamp
- Be written for the target audience (user vs developer)

### 📊 Priority Order

1. **Critical** (needed for users to use the tool):

   - installation.md
   - quickstart.md
   - user-guide/algorithms.md
   - api/endpoints.md

1. **Important** (needed for production deployment):

   - deployment/docker.md
   - deployment/configuration.md
   - deployment/troubleshooting.md
   - reference/configuration.md

1. **Valuable** (improves developer experience):

   - developer/architecture.md
   - developer/testing.md
   - algorithms/\*.md (detailed specs)

1. **Nice-to-have** (completeness):

   - reference/glossary.md
   - reference/faq.md
   - migration guides

### ✅ Next Steps

1. Create directory structure
1. Generate placeholder files with TODOs
1. Extract information from codebase
1. Populate each document systematically
1. Cross-reference and validate accuracy
1. Add diagrams where helpful
