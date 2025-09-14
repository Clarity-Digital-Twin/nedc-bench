"""Test Alpha Pipeline environment and Docker setup"""

import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_docker_build():
    """Alpha container builds successfully"""
    # Check if we're in CI or local environment
    if os.environ.get("CI"):
        result = subprocess.run(
            ["docker", "build", "-t", "nedc-alpha", "alpha/"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"


def test_environment_variables():
    """Container has correct environment"""
    if os.environ.get("CI"):
        result = subprocess.run(
            ["docker", "run", "nedc-alpha", "env"], check=False, capture_output=True, text=True
        )
        assert "NEDC_NFC=/opt/nedc" in result.stdout
        assert "PYTHONPATH=/opt/nedc/lib" in result.stdout


def test_nedc_installation_local():
    """Test NEDC installation exists locally"""
    nedc_path = Path(__file__).parent.parent / "nedc_eeg_eval" / "v6.0.0"
    assert nedc_path.exists(), f"NEDC not found at {nedc_path}"
    assert (nedc_path / "lib").exists(), "NEDC lib directory not found"
    assert (nedc_path / "bin" / "nedc_eeg_eval").exists(), "NEDC eval script not found"


def test_wrapper_imports():
    """Test that wrapper modules can be imported"""
    try:
        from alpha.wrapper import NEDCAlphaWrapper  # noqa: PLC0415
        from alpha.wrapper.parsers import TAESParser, UnifiedOutputParser  # noqa: PLC0415

        assert NEDCAlphaWrapper is not None
        assert UnifiedOutputParser is not None
        assert TAESParser is not None
    except ImportError as e:
        # This is expected if not running in Docker
        if not os.environ.get("CI"):
            print(f"Import test skipped (not in Docker): {e}")
        else:
            raise
