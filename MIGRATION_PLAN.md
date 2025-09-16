# Migration Plan: Moving to src/ Structure

## Target Structure

```
nedc-bench/
├── nedc_eeg_eval/        # STAYS AT ROOT (vendored, untouched)
├── src/
│   ├── nedc_bench/       # Our clean implementation (beta pipeline)
│   │   ├── __init__.py
│   │   ├── algorithms/
│   │   ├── api/
│   │   ├── models/
│   │   ├── orchestration/
│   │   ├── utils/
│   │   └── validation/
│   ├── alpha/            # Legacy NEDC wrapper (alpha pipeline)
│   │   ├── __init__.py
│   │   └── wrapper/
│   └── cli/              # NEW: Command-line interface
│       ├── __init__.py
│       └── main.py
├── tests/                # Stays at root
├── scripts/              # Stays at root (dev scripts)
├── data/                 # Stays at root
└── pyproject.toml        # Updated to reference src/
```

## Why This Structure Works

1. **Vendored code clearly separated**: `nedc_eeg_eval` at root = "don't touch this"
1. **Our code in src/**: Standard Python practice
1. **Clean imports**: `from nedc_bench.algorithms import TAESScorer` (no src prefix needed)
1. **Easy to package**: Can distribute without vendored code if needed

## Migration Steps

### Step 1: Create src/ and move our code

```bash
# Create new structure
mkdir -p src

# Move our implementations
mv nedc_bench src/
mv alpha src/

# Verify nothing broke
make test
```

### Step 2: Update pyproject.toml

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["nedc_bench*", "alpha*", "cli*"]

[tool.setuptools.package-dir]
"" = "src"
```

### Step 3: Fix imports in moved files

```python
# Old import in alpha/wrapper.py:
sys.path.append(os.path.join(os.path.dirname(__file__), "../nedc_eeg_eval/v6.0.0/lib"))

# New import:
sys.path.append(
    os.path.join(os.path.dirname(__file__), "../../nedc_eeg_eval/v6.0.0/lib")
)
```

### Step 4: Add compatibility layer (temporary)

```python
# nedc_bench.py at root (temporary compatibility)
"""Compatibility layer - will be removed in v2.0"""
import warnings

warnings.warn(
    "Importing from root is deprecated. Use 'from nedc_bench' instead.",
    DeprecationWarning,
)
from src.nedc_bench import *
```

### Step 5: Create CLI

```python
# src/cli/main.py
import typer
from pathlib import Path
from nedc_bench.algorithms import TAESScorer, OverlapScorer
from nedc_bench.models import AnnotationFile

app = typer.Typer(name="nedc-bench", help="Clinical-grade EEG evaluation platform")


@app.command()
def evaluate(
    reference: Path = typer.Argument(..., help="Reference CSV_BI file"),
    hypothesis: Path = typer.Argument(..., help="Hypothesis CSV_BI file"),
    algorithm: str = typer.Option("taes", help="Scoring algorithm"),
    output_format: str = typer.Option("json", help="Output format"),
):
    """Evaluate seizure detection performance"""
    ref = AnnotationFile.from_csv_bi(reference)
    hyp = AnnotationFile.from_csv_bi(hypothesis)

    scorer = {
        "taes": TAESScorer,
        "overlap": OverlapScorer,
    }[algorithm]()

    result = scorer.score(ref, hyp)
    print(result.to_json() if output_format == "json" else result)


@app.command()
def validate(
    reference: Path = typer.Argument(...),
    hypothesis: Path = typer.Argument(...),
    pipeline: str = typer.Option("dual", help="Pipeline to run (alpha/beta/dual)"),
):
    """Validate parity between pipelines"""
    # Implementation here
    pass
```

### Step 6: Update entry points

```toml
# pyproject.toml
[project.scripts]
nedc-bench = "cli.main:app"
```

## Benefits After Migration

1. **Clean separation**: Vendored vs our code is obvious
1. **Standard structure**: New developers recognize src/ pattern
1. **Better tooling**: Most Python tools expect src/ layout
1. **CLI included**: `nedc-bench evaluate ref.csv hyp.csv`
1. **Unchanged functionality**: All existing code still works

## Testing the Migration

```bash
# After moving files
cd /path/to/nedc-bench

# Reinstall in development mode
pip install -e .

# Run tests to verify nothing broke
make test

# Test CLI
nedc-bench --help
nedc-bench evaluate data/csv_bi_parity/csv_bi_export_clean/ref/aaaaaajy_s001_t000.csv_bi \
                    data/csv_bi_parity/csv_bi_export_clean/hyp/aaaaaajy_s001_t000.csv_bi \
                    --algorithm taes

# Test imports
python -c "from nedc_bench.algorithms import TAESScorer; print('✓ Import works')"
python -c "from alpha.wrapper import NEDCAlphaWrapper; print('✓ Import works')"
```

## Rollback Plan

If something goes wrong:

```bash
# Move everything back
mv src/nedc_bench ./
mv src/alpha ./
rm -rf src/

# Restore original pyproject.toml
git checkout pyproject.toml

# Verify
make test
```

## Timeline

- **Hour 1**: Move files, update pyproject.toml
- **Hour 2**: Fix any broken imports
- **Hour 3**: Add CLI
- **Hour 4**: Test everything
- **Hour 5**: Update documentation

Total: ~5 hours of work for a much cleaner structure
