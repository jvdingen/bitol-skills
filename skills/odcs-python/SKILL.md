---
name: odcs-python
description: Open Data Contract Standard (ODCS) Python implementation reference for the open-data-contract-standard PyPI package. Covers installation, the OpenDataContractStandard Pydantic model and its child models, parsing/constructing/validating/serializing contracts, the version-mapping rules between the spec and the pip module, common gotchas with strict validation (extra='forbid'), Pydantic ValidationError shapes, and short code recipes. Use when the user is reading, writing, parsing, validating, or generating ODCS contracts in Python; asks how to use the OpenDataContractStandard class; needs the spec-to-pip-module version map; or hits a Pydantic validation error from an ODCS contract. Supports ODCS spec versions 3.0.1, 3.0.2, and 3.1.0 via pip module versions ≥3.0.1, ≥3.0.4, and ≥3.1.0 respectively.
compatibility: Requires Python 3.10+ and the open-data-contract-standard PyPI package (>=3.0.1).
metadata:
  spec_versions:
    - "3.0.1"
    - "3.0.2"
    - "3.1.0"
---

# ODCS Python

The `open-data-contract-standard` PyPI package is the canonical Python implementation of the [Open Data Contract Standard](https://github.com/bitol-io/open-data-contract-standard). It is a thin layer: one Pydantic v2 model (`OpenDataContractStandard`) plus a tree of child models that mirror the YAML spec, with `from_file` / `from_string` / `to_yaml` / `json_schema` helpers. This skill teaches agents how to use it.

## When to use this skill

Activate this skill when the user is doing any of:

- Loading an ODCS YAML contract into Python.
- Constructing an ODCS contract programmatically (Python objects → YAML).
- Validating a contract via the Pydantic model and interpreting `ValidationError` output.
- Asking which pip module version to install for a given ODCS spec version.
- Hitting an error like "extra fields not permitted" when parsing a contract.
- Reading or writing tests against ODCS contracts.

Do **not** use this skill for general ODCS YAML *meaning* questions ("what does `physicalType` mean?", "how do I model a Kafka topic?"). Those are covered by the `odcs-yaml` skill. This skill is the *Python API* layer; for spec semantics, point the user at `odcs-yaml`.

Do **not** use this skill for ODPS data products. The `open-data-contract-standard` package only models ODCS *contracts*. There is no Pydantic model in this package for ODPS data products, input/output ports, or management ports — if the user wants to parse or construct ODPS YAML, they need a different library (and the `odps-yaml` skill covers the spec side).

The skills are independently installable. This skill vendors enough of the spec (a small example contract) to be self-contained.

## Mental model

The package is **deliberately minimal**. There is no validator subcommand, no migration tool, no CLI, no diff helper. All it does is:

1. **Mirror the ODCS spec as a Pydantic model tree** — `OpenDataContractStandard` at the root, with nested classes for `SchemaObject`, `SchemaProperty`, `Server`, `Team`, `TeamMember`, `DataQuality`, `Pricing`, `Role`, `Description`, `Support`, `Relationship`, `ServiceLevelAgreementProperty`, `AuthoritativeDefinition`, `CustomProperty`. See [`python/model.py`](references/python/model.py) for the full definitions.
2. **Round-trip YAML ↔ model** — `from_file(path)`, `from_string(yaml_str)`, `to_yaml()`. Validation is *implicit*: it happens during construction (Pydantic raises `ValidationError` on bad input).
3. **Expose the bundled JSON Schema** — `OpenDataContractStandard.json_schema()` returns the spec's JSON Schema as a string. The bundled schema tracks the spec version the pip module corresponds to.

The package does **not** validate against the JSON Schema. It validates against the *Pydantic model*, which is hand-maintained to match the spec. When the two disagree, the model wins for parsing — but the bundled JSON Schema is the artifact you ship to other tools.

Critical config: the root model uses `model_config = pyd.ConfigDict(extra='forbid')`. Unknown top-level fields raise `ValidationError`. This is intentional — it catches v2/v3 confusion and typos.

## Installation

```bash
pip install open-data-contract-standard
# or
uv add open-data-contract-standard
```

Requires Python 3.10+. Brings in `pydantic>=2.8.0` and `pyyaml>=6.0.0` as dependencies. See [`python/README.md`](references/python/README.md) for the upstream installation block.

## Version mapping

The pip module's major.minor tracks the spec's major.minor, **but not the patch version**. This is the table from the upstream README:

| ODCS spec version | Pip module version |
|-------------------|--------------------|
| 3.0.1             | `>=3.0.1`          |
| 3.0.2             | `>=3.0.4`          |
| 3.1.0             | `>=3.1.0`          |

Notes:
- **There is no published pip module entry for spec v3.0.0.** The lowest mapped spec version is 3.0.1. If a user hands you a `v3.0.0` contract, the closest pip module is `>=3.0.1`, which will likely parse it but may not produce identical output on round-trip.
- The patch number diverges between spec and module (e.g. spec v3.0.2 needs module ≥3.0.4). Always use the table, not your intuition.
- Pin to `>=` the listed version, not `==`. Patch releases of the module fix bugs without changing the spec target.
- The latest module as of this skill's writing is **v3.1.2**, which targets spec v3.1.0.

## Core API — code recipes

Every recipe below is grounded in [`python/model.py`](references/python/model.py) (the source) and [`python/test_model.py`](references/python/test_model.py) (the upstream test that demonstrates roundtrip).

### Parse from a file

```python
from open_data_contract_standard.model import OpenDataContractStandard

contract = OpenDataContractStandard.from_file("path/to/contract.odcs.yaml")
print(contract.id, contract.apiVersion, contract.status)
```

`from_file` raises `FileNotFoundError` if the file is missing, then delegates to `from_string`.

### Parse from a string

```python
yaml_str = """
apiVersion: v3.1.0
kind: DataContract
id: 53581432-6c55-4ba2-a65f-72344a91553b
version: 1.0.0
status: active
name: my_table
"""
contract = OpenDataContractStandard.from_string(yaml_str)
```

`from_string` calls `yaml.safe_load` and then constructs the Pydantic model. Any field that doesn't match raises `pydantic.ValidationError`.

### Construct programmatically

```python
from open_data_contract_standard.model import (
    OpenDataContractStandard,
    SchemaObject,
    SchemaProperty,
    Team,
    TeamMember,
)

contract = OpenDataContractStandard(
    apiVersion="v3.1.0",
    kind="DataContract",
    id="53581432-6c55-4ba2-a65f-72344a91553b",
    version="1.0.0",
    status="active",
    name="my_table",
    team=Team(name="data-platform", members=[TeamMember(username="alice", role="owner")]),
)
```

The full constructor surface is the field list on `OpenDataContractStandard` in [`python/model.py`](references/python/model.py) starting at line 214 — every top-level ODCS field maps to a kwarg of the same name, **with one exception** (see Gotchas).

### Serialize back to YAML

```python
print(contract.to_yaml())
```

`to_yaml()` calls `model_dump(exclude_defaults=True, exclude_none=True, by_alias=True)` and dumps with `sort_keys=False, allow_unicode=True`. The output omits `None` and default values, so a freshly-constructed minimal contract round-trips compactly. The `by_alias=True` is what makes the `schema_` field serialize back to `schema` (see Gotchas).

### Get the bundled JSON Schema

```python
schema_json_str = OpenDataContractStandard.json_schema()
```

Returns the *string* contents of the bundled `schema.json`, not a parsed dict. The bundled schema corresponds to the spec version the pip module targets (currently v3.1.0). If you need the schema as a dict, `json.loads(...)` it. The vendored copy of the bundled schema lives at [`python/schema.json`](references/python/schema.json).

### Round-trip test pattern

```python
import yaml
from open_data_contract_standard.model import OpenDataContractStandard

def assert_equals_yaml(yaml_str: str) -> None:
    parsed_then_dumped = OpenDataContractStandard.from_string(yaml_str).to_yaml()
    assert yaml.safe_load(yaml_str) == yaml.safe_load(parsed_then_dumped)
```

This is the upstream test pattern (from [`python/test_model.py`](references/python/test_model.py)) — compare *parsed* YAML on both sides, not raw strings, since the dumper may reorder keys or normalize quoting.

## Gotchas

These bite people. Most of them you can spot the moment you see the error message.

### `schema` is `schema_` in Python

Pydantic's `BaseModel.schema()` is a built-in method, so the field is declared as `schema_` with a Pydantic alias to `schema`:

```python
schema_: list[SchemaObject] | None = pyd.Field(default=None, alias="schema")
```

What this means in practice:
- **When parsing YAML**: use `schema:` in the YAML (the alias). The model accepts it.
- **When constructing in Python**: pass `schema_=...` as the kwarg, *not* `schema=...`. Or use `OpenDataContractStandard.model_validate({"schema": [...]})` to pass the alias form.
- **When reading the loaded model**: access `contract.schema_`, *not* `contract.schema`.
- **When serializing**: `to_yaml()` already passes `by_alias=True`, so `schema_` becomes `schema:` in the output. You don't need to do anything.

This is the single most common source of "field not set" surprises.

### `extra='forbid'` rejects unknown top-level fields

```python
ValidationError: 1 validation error for OpenDataContractStandard
unknownField
  Extra inputs are not permitted [type=extra_forbidden, ...]
```

Causes:
- The contract has a typo in a field name.
- The contract has a v2 field name (`columns`, `quantumName`, `datasetDomain`, `uuid`, `sampleValues`, `isNullable`, `isPrimaryKey`, …) — the lib only supports v3.
- The contract has a custom top-level extension. **Move it under `customProperties`.**
- The contract is from a newer spec version than the pip module supports.

The fix is almost always: rename the field, move it into `customProperties`, or upgrade the pip module.

### `team` accepts both the v3.0.x array form and the v3.1.0 object form

```python
team: Team | list[TeamMember] | None = None
```

The model is a `Union`, which means a v3.0.x contract that declares `team` as a list of members will parse, and so will a v3.1.0 contract that declares `team` as a `Team` object with `name`/`description`/`members`. Both round-trip. This is the lib's only spec-version-bridging behavior — be aware that `contract.team` may be either type after parsing, and code that walks it should check.

### Validation runs at construction time, not on demand

There is no `contract.validate()` method. Validation is what `from_file`, `from_string`, and the constructor *do*. If a contract has already been built into a `OpenDataContractStandard` instance, it has already been validated.

To validate a YAML file without keeping the result:

```python
try:
    OpenDataContractStandard.from_file(path)
except (FileNotFoundError, pydantic.ValidationError) as e:
    print(f"invalid: {e}")
```

### `to_yaml()` drops `None` and defaults — the output may look smaller than the input

`exclude_defaults=True, exclude_none=True` means a YAML round-trip will silently drop fields that were `null` or set to a Python default. If you're diffing input and output, expect omissions for empty/null fields. This is by design.

### The pip module does not validate against the bundled JSON Schema

`OpenDataContractStandard.json_schema()` returns the schema for *consumers* of the contract (other tools, IDE integrations). It is not used internally for validation. The model classes are hand-maintained to match the spec, and Pydantic does the validation against *those*. So passing the JSON Schema test is necessary but not sufficient — and vice versa, in rare cases.

### Pydantic v2 ValidationError shape

```python
from pydantic import ValidationError
try:
    OpenDataContractStandard.from_string(yaml_str)
except ValidationError as e:
    for err in e.errors():
        print(err["loc"], err["type"], err["msg"])
```

`err["loc"]` is a tuple of field names walking down the model tree (e.g. `("schema", 0, "properties", 2, "logicalType")`). `err["type"]` is one of `string_type`, `extra_forbidden`, `missing`, `literal_error`, etc. The `loc` plus `type` is usually enough to point a user at the exact YAML line.

## Common questions

**"How do I install it?"**
`pip install open-data-contract-standard` (or `uv add open-data-contract-standard`). Pin to `>=` the version listed in the version-mapping table for your target spec version. Requires Python 3.10+.

**"Which version supports ODCS spec v3.0.0?"**
None published. The lowest mapped spec version is 3.0.1, served by pip module `>=3.0.1`. v3.0.0 contracts will likely parse against `>=3.0.1`, but it is not officially supported.

**"How do I validate a contract?"**
Just construct it: `OpenDataContractStandard.from_file(path)`. If it raises `pydantic.ValidationError`, it's invalid. There is no separate validator method.

**"How do I extract the bundled JSON Schema?"**
`OpenDataContractStandard.json_schema()` — returns it as a string. `json.loads(...)` if you want a dict. The vendored copy is at [`python/schema.json`](references/python/schema.json).

**"Why does my `schema:` field show up as `schema_` in Python?"**
Because `schema` is a Pydantic v1 builtin method. The field uses an alias. Use `schema_` in Python and `schema:` in YAML; `to_yaml()` handles the conversion automatically via `by_alias=True`.

**"Can I use this to migrate v2 contracts to v3?"**
No. The lib only supports v3. v2 fields will trip `extra='forbid'`. Migration is a manual exercise (or a job for a separate tool).

**"Is there a CLI?"**
No. The package is a library only. The [Data Contract CLI](https://github.com/datacontract/datacontract-cli) consumes this package and provides the user-facing tooling.

**"Does the lib normalize contracts (sort fields, expand defaults)?"**
No. It dumps with `sort_keys=False` and excludes defaults/None on the way out. Round-tripping preserves field order from the *Pydantic model definition order*, not the input file order. If you care about byte-identical roundtrips, the lib is not the right tool.

## Reference index

Everything below lives in this skill's `references/` directory:

- **The model source**: [`python/model.py`](references/python/model.py) — the canonical list of every class and field. Read this to answer "does the lib expose field X?".
- **The upstream README**: [`python/README.md`](references/python/README.md) — install, usage, version-mapping table.
- **The bundled JSON Schema**: [`python/schema.json`](references/python/schema.json) — what `OpenDataContractStandard.json_schema()` returns. Currently corresponds to spec v3.1.0.
- **Upstream tests**: [`python/test_model.py`](references/python/test_model.py) — small but it documents the round-trip pattern.
- **Example contract**: [`examples/table-column.odcs.yaml`](references/examples/table-column.odcs.yaml) — a small valid v3.1.0 contract you can hand to `from_file` for a smoke test.

When answering a question, prefer pointing the user at `python/model.py` for "does field X exist" and at `python/test_model.py` for "what's the idiomatic pattern" — those are the sources of truth.
