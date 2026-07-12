"""Tests for the odcs-yaml skill's bundled contract validator.

The script is exercised end-to-end via subprocess, the same way an agent
invokes it, so exit codes and stderr behavior are covered — not just the
internal functions. The test venv has pyyaml + jsonschema but NOT the
open-data-contract-standard package, so these tests cover the JSON Schema
fallback path (the path a fresh skill install hits).
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "skills" / "odcs-yaml" / "scripts" / "validate_contract.py"
EXAMPLES = sorted(REPO_ROOT.glob("skills/odcs-yaml/references/examples/*.yaml"))


def run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_examples_are_discovered() -> None:
    assert EXAMPLES, "no vendored ODCS examples found — has vendoring run?"


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.name)
def test_vendored_examples_validate(example: Path) -> None:
    """Every vendored example must pass the skill's own validator.

    This catches drift between the vendored examples and the vendored
    schemas — e.g. an upstream example bumping to an apiVersion we do not
    vendor a schema for.
    """
    proc = run_validator(str(example))
    assert proc.returncode == 0, f"stderr: {proc.stderr}\nstdout: {proc.stdout}"


def test_empty_file_fails_cleanly(tmp_path: Path) -> None:
    contract = tmp_path / "empty.odcs.yaml"
    contract.write_text("")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert "not a YAML mapping" in proc.stderr


def test_list_root_fails_cleanly(tmp_path: Path) -> None:
    contract = tmp_path / "list.odcs.yaml"
    contract.write_text("- a\n- b\n")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "not a YAML mapping" in proc.stderr


def test_missing_api_version_fails(tmp_path: Path) -> None:
    contract = tmp_path / "noversion.odcs.yaml"
    contract.write_text("kind: DataContract\nid: x\n")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "apiVersion" in proc.stderr


def test_unknown_api_version_lists_supported(tmp_path: Path) -> None:
    contract = tmp_path / "unknown.odcs.yaml"
    contract.write_text(
        "apiVersion: v99.0.0\nkind: DataContract\nid: x\nversion: 1.0.0\nstatus: active\n"
    )
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "unknown apiVersion" in proc.stderr
    # supported versions are discovered from references/schemas/, not hardcoded
    assert "v3.1.0" in proc.stderr


def test_invalid_contract_fails(tmp_path: Path) -> None:
    contract = tmp_path / "invalid.odcs.yaml"
    contract.write_text("apiVersion: v3.1.0\nkind: DataContract\nid: x\n")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "FAIL" in proc.stderr


def test_missing_file_fails() -> None:
    proc = run_validator("does-not-exist.odcs.yaml")
    assert proc.returncode == 1
    assert "not found" in proc.stderr
