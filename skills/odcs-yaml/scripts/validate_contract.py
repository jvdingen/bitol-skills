#!/usr/bin/env python3
"""Validate an ODCS contract YAML.

Runs two complementary checks:

1. JSON Schema validation against the vendored schema matching the
   contract's apiVersion. This is authoritative for required fields — the
   Bitol Pydantic model marks every field Optional, so it cannot catch a
   missing `version` or `status`.
2. The Bitol Pydantic model (open-data-contract-standard), when installed.
   It adds type strictness and unknown-field rejection. Its rejection is
   only treated as final when the installed module targets the same spec
   major.minor as the contract's apiVersion (the module's major.minor
   tracks the spec's); for a contract from a different spec line, a
   rejection is reported as a note and the version-matched schema decides.

Designed to run via `uv run` so dependencies are handled automatically:

    uv run --with open-data-contract-standard --with pyyaml --with jsonschema \
        scripts/validate_contract.py contract.odcs.yaml

Or directly if the dependencies are already available:

    python3 scripts/validate_contract.py contract.odcs.yaml
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = SKILL_ROOT / "references" / "schemas"


def _discover_schemas() -> dict[str, Path]:
    """Map apiVersion (e.g. 'v3.1.0') to its vendored schema file.

    Discovered from references/schemas/ rather than hardcoded, so vendoring a
    new spec version's schema automatically extends what this script accepts.
    """
    return {
        p.stem.removeprefix("odcs-json-schema-"): p
        for p in sorted(SCHEMAS_DIR.glob("odcs-json-schema-v*.json"))
    }

NOT_VALIDATED_MSG = (
    "WARNING: contract was NOT validated. "
    "Install pyyaml and jsonschema, or use: "
    "uv run --with pyyaml --with jsonschema scripts/validate_contract.py <file>"
)


def _load_yaml(path: Path) -> object:
    try:
        import yaml
    except ImportError:
        print(NOT_VALIDATED_MSG, file=sys.stderr)
        print("  missing dependency: pyyaml", file=sys.stderr)
        sys.exit(3)

    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"FAIL: YAML parse error: {exc}", file=sys.stderr)
        sys.exit(1)


def _try_pydantic(path: Path) -> tuple[bool, str | None] | None:
    """Try validating with the Bitol Pydantic model.

    Returns None if the package isn't installed (we don't force-install it);
    otherwise (ok, error_message)."""
    try:
        from open_data_contract_standard.model import OpenDataContractStandard
    except ImportError:
        return None

    try:
        OpenDataContractStandard.from_file(str(path))
        return (True, None)
    except Exception as exc:
        return (False, str(exc))


def _installed_module_spec_mm() -> str | None:
    """major.minor of the installed open-data-contract-standard module.

    The module's major.minor tracks the spec's major.minor (patch versions
    diverge), so this is the spec line the module's model targets."""
    try:
        from importlib.metadata import version

        parts = version("open-data-contract-standard").split(".")
    except Exception:
        return None
    return ".".join(parts[:2]) if len(parts) >= 2 else None


def _contract_spec_mm(api_version: str) -> str:
    """major.minor of a contract's apiVersion, e.g. 'v3.0.2' -> '3.0'."""
    return ".".join(api_version.lstrip("v").split(".")[:2])


def _validate_jsonschema(contract: dict, api_version: str) -> bool:
    schemas = _discover_schemas()
    if not schemas:
        print(f"FAIL: no vendored schemas found in {SCHEMAS_DIR}", file=sys.stderr)
        return False

    schema_path = schemas.get(api_version)
    if not schema_path:
        print(
            f"FAIL: unknown apiVersion '{api_version}'. "
            f"Supported: {', '.join(sorted(schemas))}",
            file=sys.stderr,
        )
        return False

    try:
        import jsonschema
    except ImportError:
        print(NOT_VALIDATED_MSG, file=sys.stderr)
        print("  missing dependency: jsonschema", file=sys.stderr)
        sys.exit(3)

    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(contract, schema)
        return True
    except jsonschema.ValidationError as exc:
        print(f"FAIL (jsonschema): {exc.message}", file=sys.stderr)
        if exc.absolute_path:
            print(f"  at: {'.'.join(str(p) for p in exc.absolute_path)}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(f"Usage: {sys.argv[0]} <contract.odcs.yaml>", file=sys.stderr)
        return 2

    path = Path(argv[0])
    if not path.exists():
        print(f"FAIL: file not found: {path}", file=sys.stderr)
        return 1

    contract = _load_yaml(path)
    if not isinstance(contract, dict):
        print(
            "FAIL: contract is not a YAML mapping at the root "
            "(empty file, a list, or a scalar)",
            file=sys.stderr,
        )
        return 1
    api_version = contract.get("apiVersion", "")
    if not isinstance(api_version, str) or not api_version:
        print("FAIL: contract has no 'apiVersion' string field", file=sys.stderr)
        return 1

    pydantic_result = _try_pydantic(path)
    if pydantic_result is not None and not pydantic_result[0]:
        # Pydantic rejected the contract. Its verdict is final only when the
        # installed module targets this contract's spec line — otherwise the
        # rejection may just be version skew, and the version-matched
        # vendored schema decides.
        _, pydantic_error = pydantic_result
        module_mm = _installed_module_spec_mm()
        if module_mm is not None and module_mm == _contract_spec_mm(api_version):
            print(f"FAIL (pydantic): {pydantic_error}", file=sys.stderr)
            return 1
        print(
            f"note: the installed open-data-contract-standard module "
            f"(spec {module_mm or 'unknown'}.x) rejected this {api_version} "
            f"contract; deferring to the version-matched JSON Schema. "
            f"Pydantic error: {pydantic_error}",
            file=sys.stderr,
        )

    # JSON Schema runs even when pydantic passed: the pydantic model marks
    # every field Optional, so only the schema enforces required fields.
    if not _validate_jsonschema(contract, api_version):
        return 1

    if pydantic_result is not None and pydantic_result[0]:
        print(f"OK (pydantic + jsonschema against {api_version}): {path}")
    else:
        print(f"OK (jsonschema against {api_version}): {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
