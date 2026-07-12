"""Tests for the odcs-yaml skill's bundled contract validator.

The script is exercised end-to-end via subprocess, the same way an agent
invokes it, so exit codes and stderr behavior are covered — not just the
internal functions. The test venv has pyyaml, jsonschema, AND the
open-data-contract-standard package, so both validation layers run: the
version-matched JSON Schema (authoritative for required fields) and the
Bitol Pydantic model (type strictness). The version-skew fall-through is
covered in-process with a monkeypatched pydantic verdict.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "skills" / "odcs-yaml" / "scripts" / "validate_contract.py"
EXAMPLES = sorted(REPO_ROOT.glob("skills/odcs-yaml/references/examples/*.yaml"))


def _load_script_module():
    spec = importlib.util.spec_from_file_location("validate_contract", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_missing_required_fields_fail_despite_pydantic(tmp_path: Path) -> None:
    """The pydantic model marks every field Optional, so it accepts a contract
    missing `version` and `status`. The JSON Schema check must still fail it."""
    contract = tmp_path / "invalid.odcs.yaml"
    contract.write_text("apiVersion: v3.1.0\nkind: DataContract\nid: x\n")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "required" in proc.stderr


def test_malformed_yaml_fails_cleanly(tmp_path: Path) -> None:
    contract = tmp_path / "broken.odcs.yaml"
    contract.write_text("apiVersion: v3.1.0\n  bad:\nindent: [unclosed\n")
    proc = run_validator(str(contract))
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr


def test_missing_file_fails() -> None:
    proc = run_validator("does-not-exist.odcs.yaml")
    assert proc.returncode == 1
    assert "not found" in proc.stderr


def test_valid_contract_reports_both_checks(tmp_path: Path) -> None:
    """With the package installed, a valid contract passes both layers."""
    example = REPO_ROOT / "skills/odcs-yaml/references/examples/full-example.odcs.yaml"
    proc = run_validator(str(example))
    assert proc.returncode == 0
    assert "pydantic + jsonschema" in proc.stdout


def test_pydantic_rejection_final_on_matching_spec_line(monkeypatch, tmp_path: Path) -> None:
    """A pydantic rejection is final when the module targets the contract's
    spec major.minor."""
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_try_pydantic", lambda p: (False, "boom"))
    monkeypatch.setattr(mod, "_installed_module_spec_mm", lambda: "3.1")
    contract = tmp_path / "c.odcs.yaml"
    contract.write_text(
        "apiVersion: v3.1.0\nkind: DataContract\nid: x\nversion: 1.0.0\nstatus: active\n"
    )
    assert mod.main([str(contract)]) == 1


def test_pydantic_rejection_deferred_on_version_skew(monkeypatch, capsys) -> None:
    """A pydantic rejection of a contract from a different spec line defers to
    the version-matched vendored schema."""
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_try_pydantic", lambda p: (False, "boom"))
    monkeypatch.setattr(mod, "_installed_module_spec_mm", lambda: "3.1")
    # vendored example declares apiVersion v3.0.2 and passes its schema
    example = REPO_ROOT / "skills/odcs-yaml/references/examples/table-column.odcs.yaml"
    assert mod.main([str(example)]) == 0
    captured = capsys.readouterr()
    assert "deferring to the version-matched JSON Schema" in captured.err
    assert "OK (jsonschema against v3.0.2)" in captured.out
