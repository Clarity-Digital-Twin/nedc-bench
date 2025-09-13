"""Pytest configuration and fixtures for NEDC-BENCH tests."""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def nedc_root(project_root: Path) -> Path:
    """Get the NEDC evaluation tool root directory."""
    return project_root / "nedc_eeg_eval" / "v6.0.0"


@pytest.fixture
def test_data_dir(nedc_root: Path) -> Path:
    """Get the test data directory."""
    return nedc_root / "data" / "csv"


@pytest.fixture
def ref_list_file(nedc_root: Path) -> Path:
    """Get the reference list file path."""
    return nedc_root / "data" / "lists" / "ref.list"


@pytest.fixture
def hyp_list_file(nedc_root: Path) -> Path:
    """Get the hypothesis list file path."""
    return nedc_root / "data" / "lists" / "hyp.list"


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    # Cleanup happens automatically with tmp_path


@pytest.fixture(autouse=True)
def setup_nedc_env(nedc_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up NEDC environment variables for tests."""
    monkeypatch.setenv("NEDC_NFC", str(nedc_root))
    pythonpath = os.environ.get("PYTHONPATH", "")
    lib_path = str(nedc_root / "lib")
    if lib_path not in pythonpath:
        new_pythonpath = f"{lib_path}:{pythonpath}" if pythonpath else lib_path
        monkeypatch.setenv("PYTHONPATH", new_pythonpath)