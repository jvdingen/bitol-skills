#!/usr/bin/env python3
"""Validate an ODCS contract YAML against the vendored JSON Schema.

Tries the Bitol Pydantic model first (strictest validation). Falls back to
JSON Schema validation using the vendored schemas shipped with this skill.

Designed to run via `uv run` so dependencies are handled automatically:

    uv run --with pyyaml --with jsonschema scripts/validate_contract.py contract.odcs.yaml

Or directly if pyyaml and jsonschema are already available:

    python3 scripts/validate_contract.py contract.odcs.yaml
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = SKILL_ROOT / "references" / "schemas"

SCHEMA_FILES = {
    "v3.0.0": "odcs-json-schema-v3.0.0.json",
    "v3.0.1": "odcs-json-schema-v3.0.1.json",
    "v3.0.2": "odcs-json-schema-v3.0.2.json",
    "v3.1.0": "odcs-json-schema-v3.1.0.json",
}

NOT_VALIDATED_MSG = (
    "WARNING: contract was NOT validated. "
    "Install pyyaml and jsonschema, or use: "
    "uv run --with pyyaml --with jsonschema scripts/validate_contract.py <file>"
)


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        print(NOT_VALIDATED_MSG, file=sys.stderr)
        print("  missing dependency: pyyaml", file=sys.stderr)
        sys.exit(3)

    with open(path) as f:
        return yaml.safe_load(f)


def _try_pydantic(path: Path) -> bool | None:
    """Try validating with the Bitol Pydantic model. Returns True/False, or
    None if the package isn't installed and we shouldn't force-install it."""
    try:
        from open_data_contract_standard.model import OpenDataContractStandard
    except ImportError:
        return None

    try:
        OpenDataContractStandard.from_file(str(path))
        return True
    except Exception as exc:
        print(f"FAIL (pydantic): {exc}", file=sys.stderr)
        return False


def _validate_jsonschema(contract: dict, api_version: str) -> bool:
    schema_file = SCHEMA_FILES.get(api_version)
    if not schema_file:
        print(
            f"FAIL: unknown apiVersion '{api_version}'. "
            f"Supported: {', '.join(sorted(SCHEMA_FILES))}",
            file=sys.stderr,
        )
        return False

    schema_path = SCHEMAS_DIR / schema_file
    if not schema_path.exists():
        print(f"FAIL: schema file not found at {schema_path}", file=sys.stderr)
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


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <contract.odcs.yaml>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: file not found: {path}", file=sys.stderr)
        return 1

    # Try Pydantic first (if already installed)
    result = _try_pydantic(path)
    if result is True:
        print(f"OK (pydantic): {path}")
        return 0
    if result is False:
        return 1

    # Fall back to JSON Schema
    contract = _load_yaml(path)
    api_version = contract.get("apiVersion", "")
    if not api_version:
        print("FAIL: contract has no 'apiVersion' field", file=sys.stderr)
        return 1

    if _validate_jsonschema(contract, api_version):
        print(f"OK (jsonschema against {api_version}): {path}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
