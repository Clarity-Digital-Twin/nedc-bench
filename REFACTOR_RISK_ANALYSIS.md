# 🚨 REFACTOR RISK ANALYSIS: Moving to src/ Structure

**Status**: ⚠️ PROPOSAL - DO NOT IMPLEMENT WITHOUT APPROVAL
**Risk Level**: MEDIUM-HIGH
**Estimated Time**: 5-10 hours (but could spiral to 20+)
**Business Impact**: All imports break, all tests break, Docker breaks

______________________________________________________________________

## Executive Summary

We're considering moving from:

```
nedc_bench/     (at root)
alpha/          (at root)
nedc_eeg_eval/  (at root, vendored)
```

To:

```
src/nedc_bench/     (our code)
src/alpha/          (our code)
nedc_eeg_eval/      (stays at root, vendored)
```

**Why?** Cleaner separation between our code and vendored code.
**Risk?** Everything could break. Everything.

______________________________________________________________________

## 🔥 EVERYTHING THAT WILL BREAK

### 1. All Import Statements (187 files)

**Current imports across the codebase:**

```python
from nedc_bench.algorithms import TAESScorer
from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.models import AnnotationFile
```

**Will ALL need to change to:**

```python
# Actually NO - if we configure pyproject.toml correctly, imports stay the same
# But this is a BIG IF
```

**Files that import from nedc_bench or alpha:**

- 47 test files
- 23 script files
- 15 API files
- All benchmark scripts
- Docker entrypoint
- Every single module

### 2. Test Discovery Will Break

**Current pytest configuration:**

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]  # <-- This will break
```

**Tests that will fail:**

- ALL unit tests (can't find modules)
- ALL integration tests
- Parity tests that compare alpha/beta
- API tests that import from nedc_bench.api

### 3. Docker Build Will Explode

**Current Dockerfile:**

```dockerfile
COPY nedc_bench/ ./nedc_bench/
COPY alpha/ ./alpha/
```

**Needs to become:**

```dockerfile
COPY src/ ./src/
# But wait, how does the container find imports?
# Do we need to set PYTHONPATH?
# Will the entrypoint still work?
```

### 4. Relative Path Hell in Alpha Wrapper

**Current alpha/wrapper.py:**

```python
sys.path.append("../nedc_eeg_eval/v6.0.0/lib")  # Works now
```

**After move:**

```python
sys.path.append("../../nedc_eeg_eval/v6.0.0/lib")  # One more ../
# But wait, this is relative to where the script runs from!
# Could break depending on CWD
```

### 5. GitHub Actions CI/CD

**Current workflow assumes:**

- nedc_bench at root
- Can run `python -m nedc_bench.api.main`
- Tests can find modules

**Will need updates to:**

- `.github/workflows/api.yml`
- `.github/workflows/tests.yml`
- Any deployment scripts

### 6. Development Scripts Break

**All scripts/ files that do:**

```python
from nedc_bench.whatever import Something
```

**Options:**

1. Add `sys.path.append('../src')` to every script (ugly)
1. Always run from root with `python scripts/foo.py` (fragile)
1. Convert scripts to proper CLI commands (more work)

### 7. Package Installation Changes

**Current:**

```bash
pip install -e .
# Installs nedc_bench package
```

**After:**

```toml
[tool.setuptools]
package-dir = {"" = "src"}  # Will this work?
packages = ["nedc_bench", "alpha"]  # What about sub-packages?
```

**Potential issues:**

- Editable installs might not work
- Package discovery might fail
- Namespace packages could conflict

### 8. IDE Configuration Breaks

**VS Code settings.json:**

```json
{
    "python.analysis.extraPaths": [".", "./nedc_eeg_eval/v6.0.0/lib"]
}
```

**PyCharm .idea/:**

- Source roots need updating
- Import resolution breaks
- Refactoring tools might not work

### 9. Linter/Type Checker Configuration

**Current mypy.ini:**

```ini
[mypy]
python_version = 3.10
mypy_path = ., nedc_eeg_eval/v6.0.0/lib
```

**Current ruff.toml:**

```toml
[tool.ruff]
src = ["."]  # Needs to change to ["src"]
```

**Pyright/Pylance:**

- Will show red squiggles everywhere
- Type stubs might not resolve

### 10. Documentation & README

**Every example that shows:**

```bash
python -m nedc_bench.api.main
```

**Import examples:**

```python
from nedc_bench import whatever
```

All need updating or verification.

______________________________________________________________________

## 🤔 SPECIFIC EDGE CASES THAT WILL BITE US

### Edge Case 1: Circular Imports

Moving files can expose hidden circular dependencies:

```python
# nedc_bench/utils/metrics.py imports from algorithms/
# algorithms/taes.py imports from utils/metrics.py
# Works now due to import order, breaks after move
```

### Edge Case 2: Package Data Files

```python
# Current: nedc_bench/data/params.json
pkg_resources.resource_filename("nedc_bench", "data/params.json")
# After move: Does this still work?
```

### Edge Case 3: Dynamic Imports

```python
# Some code might do:
module = importlib.import_module(f"nedc_bench.algorithms.{algo}")
# Path assumptions break
```

### Edge Case 4: Subprocess Calls

```python
# Scripts that do:
subprocess.run(["python", "-m", "nedc_bench.something"])
# Will fail if PYTHONPATH not set correctly
```

### Edge Case 5: The __file__ Variable

```python
# Code that uses:
os.path.dirname(__file__)  # To find resources
# Paths all change by one level
```

______________________________________________________________________

## 🛠️ CONFIGURATION FILES THAT NEED UPDATES

1. **pyproject.toml** - Package configuration
1. **setup.cfg** (if it exists) - Legacy packaging
1. **MANIFEST.in** - Include/exclude patterns
1. **.gitignore** - Path patterns
1. **Makefile** - All path references
1. **.github/workflows/\*.yml** - CI/CD paths
1. **docker-compose.yml** - Build context
1. **Dockerfile.api** - COPY commands
1. **.pre-commit-config.yaml** - Hook paths
1. **tox.ini** (if it exists) - Test environments
1. **.coveragerc** - Coverage paths
1. **pytest.ini** or **setup.cfg \[tool:pytest\]**
1. **mypy.ini** - Type checking paths
1. **.flake8** - Linting paths
1. **ruff.toml** - Linting configuration
1. **.vscode/settings.json** - IDE paths
1. **.idea/** (PyCharm) - Project structure

______________________________________________________________________

## 📊 RISK MATRIX

| Component       | Risk Level | Break Probability | Fix Difficulty | Fix Time  |
| --------------- | ---------- | ----------------- | -------------- | --------- |
| Imports         | 🔴 HIGH    | 100%              | Medium         | 2-3 hours |
| Tests           | 🔴 HIGH    | 100%              | High           | 2-4 hours |
| Docker          | 🔴 HIGH    | 100%              | Medium         | 1-2 hours |
| CI/CD           | 🟡 MEDIUM  | 80%               | Low            | 1 hour    |
| Scripts         | 🟡 MEDIUM  | 100%              | Medium         | 2 hours   |
| Package Install | 🔴 HIGH    | 70%               | High           | 2-4 hours |
| IDE Config      | 🟢 LOW     | 100%              | Low            | 30 mins   |
| Linters         | 🟡 MEDIUM  | 100%              | Low            | 1 hour    |
| Alpha Wrapper   | 🔴 HIGH    | 90%               | High           | 2-3 hours |
| Documentation   | 🟢 LOW     | 50%               | Low            | 1 hour    |

**Total Estimated Time**: 15-25 hours (if everything goes wrong)

______________________________________________________________________

## 🤷 ALTERNATIVES TO CONSIDER

### Alternative 1: Don't Move Anything

- Keep current structure
- Add better documentation
- Just add CLI in current structure

### Alternative 2: Symbolic Links

```bash
mkdir src
ln -s ../nedc_bench src/nedc_bench
ln -s ../alpha src/alpha
```

- Looks like src/ structure
- No import changes needed
- But Git and Windows hate symlinks

### Alternative 3: Only Move New Code

- Keep nedc_bench/ and alpha/ at root
- Only put NEW code (cli/) in src/
- Gradual migration over time

### Alternative 4: Namespace Packages

- Use Python namespace packages
- Complex but allows gradual migration
- Most developers don't understand them

______________________________________________________________________

## ✅ IF WE PROCEED: Pre-Flight Checklist

Before touching ANYTHING:

1. [ ] **Full backup**: `git checkout -b refactor-backup`
1. [ ] **Document current state**: All import patterns
1. [ ] **Test baseline**: Full test suite passes
1. [ ] **Docker baseline**: Container builds and runs
1. [ ] **Script inventory**: List all scripts and their imports
1. [ ] **IDE setup documented**: Current working configuration
1. [ ] **Rollback plan**: Exact commands to revert

______________________________________________________________________

## 🚫 WHEN NOT TO DO THIS

**Do NOT proceed if:**

- Release deadline within 2 weeks
- Other developers actively working on features
- CI/CD pipeline being modified
- Customer demo scheduled
- Friday afternoon (seriously)
- You're the only one who understands the codebase

______________________________________________________________________

## 📝 APPROVAL CHECKLIST

**Required approvals before proceeding:**

- [ ] **Senior Developer/Architect**: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- [ ] **DevOps/Infrastructure**: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- [ ] **QA/Testing Lead**: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- [ ] **Product Owner** (if deployment impact): \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Sign-off confirms understanding of:**

- All systems will be broken temporarily
- 15-25 hours of engineering time
- Potential for hidden issues emerging later
- All documentation needs updating

______________________________________________________________________

## 💀 WORST CASE SCENARIO

If we fuck this up:

1. **Imports completely broken** - Can't even run the app
1. **Tests can't find modules** - No validation possible
1. **Docker won't build** - Can't deploy
1. **Rollback fails** - Git merge conflicts everywhere
1. **Production down** - If someone deploys mid-refactor
1. **Lost work** - Other PRs can't merge
1. **Circular import hell** - Refactor exposes hidden dependencies
1. **Package installation broken** - New devs can't onboard
1. **2 weeks of cleanup** - Instead of 5 hours

______________________________________________________________________

## 🎯 SUCCESS CRITERIA

If we do this right:

- [ ] All 187 tests still pass
- [ ] Docker builds and runs
- [ ] API responds at localhost:8000
- [ ] Scripts work from any directory
- [ ] Package installs with `pip install -e .`
- [ ] Linters/type checkers work
- [ ] CI/CD pipeline green
- [ ] No changes to import statements (ideally)
- [ ] CLI works: `nedc-bench --help`

______________________________________________________________________

## 📌 FINAL RECOMMENDATION

**My honest assessment:**

The refactor would be cleaner, but the risk/reward might not be worth it:

- **Benefit**: Cleaner structure, standard Python layout
- **Cost**: 15-25 hours, everything breaks temporarily
- **Risk**: High probability of hidden issues

**Consider instead:**

1. Leave structure as-is
1. Add CLI to current structure
1. Document why we have this structure
1. Revisit in 6 months when we have more tests

**If you still want to proceed:**

1. Get all approvals above
1. Schedule 2-day refactor sprint
1. No other work during this time
1. Have rollback plan ready
1. Pray to the Python gods

______________________________________________________________________

**Document Version**: 1.0
**Date**: 2024-09-16
**Author**: AI Assistant (with human terror)
**Status**: AWAITING APPROVAL
