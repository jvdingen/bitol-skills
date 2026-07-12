#!/usr/bin/env python3
"""Generate an ODCS contract for the jaffle_shop `customers` mart from DuckDB.

Introspects the live table with DESCRIBE, maps DuckDB column types onto ODCS
logical types, and builds the contract with the `open-data-contract-standard`
Pydantic model. Walked through step by step in docs/tutorials/odcs-python.md.

Run from docs/tutorials/jaffle-shop/ (after setup_jaffle_shop.sql):

    uv run --with duckdb --with open-data-contract-standard \
        scripts/generate_contract.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb
from open_data_contract_standard.model import (
    Description,
    OpenDataContractStandard,
    SchemaObject,
    SchemaProperty,
    Server,
    Team,
    TeamMember,
)

HERE = Path(__file__).resolve().parent.parent  # docs/tutorials/jaffle-shop/
DB_FILE = HERE / "jaffle_shop.duckdb"
OUT_FILE = HERE / "contracts" / "customers.odcs.yaml"

# DuckDB type -> ODCS logicalType. DECIMAL/DOUBLE map to "number"; anything
# not listed falls back to "string".
LOGICAL_TYPES = {
    "INTEGER": "integer",
    "BIGINT": "integer",
    "DOUBLE": "number",
    "DATE": "date",
    "TIMESTAMP": "timestamp",  # logicalType added in ODCS v3.1.0
    "BOOLEAN": "boolean",
    "VARCHAR": "string",
}

# Hand-written business context — the part introspection cannot know.
DESCRIPTIONS = {
    "customer_id": "Customer primary key, carried over from raw_customers.id.",
    "first_name": "Customer first name.",
    "last_name": "Customer last initial (anonymized, e.g. \"P.\").",
    "first_order": "Date of the customer's first order; null if they never ordered.",
    "most_recent_order": "Date of the customer's latest order; null if they never ordered.",
    "number_of_orders": "Lifetime count of orders placed (0 for customers with no orders).",
    "customer_lifetime_value": "Lifetime sum of order totals in USD (0.00 for customers with no orders).",
}
PRIMARY_KEY = "customer_id"
# Aggregates over the orders LEFT JOIN are null/0 for customers who never
# ordered, so only identity columns are promised non-null.
REQUIRED = {"customer_id", "first_name", "last_name", "number_of_orders",
            "customer_lifetime_value"}


def logical_type(duckdb_type: str) -> str:
    if duckdb_type.startswith("DECIMAL"):
        return "number"
    return LOGICAL_TYPES.get(duckdb_type, "string")


def introspect(table: str) -> list[SchemaProperty]:
    """Turn `DESCRIBE <table>` output into a list of SchemaProperty."""
    with duckdb.connect(str(DB_FILE), read_only=True) as con:
        rows = con.sql(f"DESCRIBE {table}").fetchall()

    properties = []
    for i, (column_name, column_type, *_rest) in enumerate(rows, start=1):
        properties.append(
            SchemaProperty(
                name=column_name,
                logicalType=logical_type(column_type),
                physicalType=column_type,
                description=DESCRIPTIONS.get(column_name),
                primaryKey=column_name == PRIMARY_KEY,
                primaryKeyPosition=1 if column_name == PRIMARY_KEY else None,
                required=column_name in REQUIRED,
                unique=column_name == PRIMARY_KEY,
            )
        )
    return properties


def build_contract() -> OpenDataContractStandard:
    customers = SchemaObject(
        name="customers",
        physicalName="customers",
        physicalType="table",
        businessName="Jaffle Shop customers",
        description="Dimension table with one row per customer and their order history rolled up.",
        dataGranularityDescription="One row per customer (customer_id is unique).",
        properties=introspect("customers"),
    )

    return OpenDataContractStandard(
        apiVersion="v3.1.0",
        kind="DataContract",
        id="7fb49248-5e36-486d-a110-d7edcf2b2e84",
        name="customers",
        version="1.0.0",
        status="active",
        domain="jaffle-shop",
        dataProduct="jaffle_shop",
        tenant="JaffleShopInc",
        description=Description(
            purpose="One row per customer with rolled-up order history (first/latest order, order count, lifetime value).",
            limitations="Includes customers with zero orders; date columns are null for them. Amounts are in USD.",
            usage="Customer segmentation, retention analysis, and lifetime-value reporting.",
        ),
        tags=["jaffle-shop", "customers"],
        # NOTE: construct with `schema=` (the YAML alias). The field is stored
        # as `schema_` — read it back as contract.schema_ — but the constructor
        # only accepts the alias, and serialization emits `schema:` again.
        schema=[customers],
        servers=[
            Server(
                server="local-duckdb",
                type="duckdb",
                environment="dev",
                database="jaffle_shop.duckdb",
                schema="main",
                description="Local DuckDB file built by setup_jaffle_shop.sql.",
            )
        ],
        team=Team(
            name="jaffle-analytics",
            description="Analytics engineering team owning the jaffle shop marts.",
            members=[
                TeamMember(
                    username="alice@jaffleshop.example",
                    name="Alice Ordway",
                    role="owner",
                )
            ],
        ),
    )


def main() -> None:
    contract = build_contract()

    # Round-trip sanity check: what we serialize must parse back cleanly.
    OpenDataContractStandard.from_string(contract.to_yaml())

    header = (
        "# Data contract for the jaffle_shop `customers` mart.\n"
        "# GENERATED by scripts/generate_contract.py (docs/tutorials/odcs-python.md)\n"
        "# from the live DuckDB catalog — do not edit by hand, regenerate instead.\n"
    )
    OUT_FILE.write_text(header + contract.to_yaml())
    print(f"wrote {OUT_FILE.relative_to(HERE)}")
    print(f"  {len(contract.schema_[0].properties)} properties introspected from DuckDB")


if __name__ == "__main__":
    main()
