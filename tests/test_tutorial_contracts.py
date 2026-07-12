"""Validate the jaffle shop tutorial artifacts (docs/tutorials/).

The tutorials commit their finished ODCS contracts and ODPS product so
readers can diff their work. These tests keep those artifacts honest as the
vendored schemas evolve:

  - every tutorial ODCS contract passes the odcs-yaml skill's validator
    (same two-layer check the tutorials themselves run);
  - the tutorial ODPS product validates against the vendored v1.0.0 schema;
  - the product's contractId references resolve to committed contracts.
"""

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = REPO_ROOT / "docs" / "tutorials" / "jaffle-shop" / "contracts"
ODCS_VALIDATOR = REPO_ROOT / "skills" / "odcs-yaml" / "scripts" / "validate_contract.py"
ODPS_SCHEMA = (
    REPO_ROOT / "skills" / "odps-yaml" / "references" / "schemas"
    / "odps-json-schema-v1.0.0.json"
)

ODCS_CONTRACTS = sorted(CONTRACTS_DIR.glob("*.odcs.yaml"))
ODPS_PRODUCTS = sorted(CONTRACTS_DIR.glob("*.odps.yaml"))


def test_tutorial_artifacts_are_discovered() -> None:
    assert len(ODCS_CONTRACTS) == 3, f"expected 3 ODCS contracts, found {ODCS_CONTRACTS}"
    assert len(ODPS_PRODUCTS) == 1, f"expected 1 ODPS product, found {ODPS_PRODUCTS}"


@pytest.mark.parametrize("contract", ODCS_CONTRACTS, ids=lambda p: p.name)
def test_tutorial_odcs_contracts_validate(contract: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ODCS_VALIDATOR), str(contract)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}\nstdout: {proc.stdout}"


@pytest.mark.parametrize("product", ODPS_PRODUCTS, ids=lambda p: p.name)
def test_tutorial_odps_product_validates(product: Path) -> None:
    with product.open(encoding="utf-8") as f:
        instance = yaml.safe_load(f)
    with ODPS_SCHEMA.open(encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance, schema)


def test_product_port_references_resolve() -> None:
    """Every contractId in the product must be the id of a committed contract."""
    contract_ids = {
        yaml.safe_load(p.read_text(encoding="utf-8"))["id"] for p in ODCS_CONTRACTS
    }
    product = yaml.safe_load(ODPS_PRODUCTS[0].read_text(encoding="utf-8"))

    referenced = set()
    for port in product.get("inputPorts", []) + product.get("outputPorts", []):
        referenced.add(port["contractId"])
        for lineage in port.get("inputContracts", []):
            referenced.add(lineage.get("id") or lineage.get("contractId"))

    unresolved = referenced - contract_ids
    assert not unresolved, f"product references unknown contract ids: {unresolved}"
