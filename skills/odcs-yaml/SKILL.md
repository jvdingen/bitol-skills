---
name: odcs-yaml
description: Open Data Contract Standard (ODCS) reference for the YAML data contract format. Covers structure, semantics, top-level sections (fundamentals, schema, data quality, SLA, servers, support, team, roles, pricing, custom properties), version differences, and how to model a dataset as a contract. Use when the user is writing, reading, validating, debugging, or migrating an ODCS contract YAML; asks about ODCS fields or sections; needs to understand the v3 object/property/element schema model; or wants to know what changed between ODCS versions. Supports ODCS spec versions 3.0.0, 3.0.1, 3.0.2, and 3.1.0. Vendored references include the per-version JSON Schemas, the full v3.1.0 prose docs, the CHANGELOG, and three representative example contracts.
metadata:
  spec_versions:
    - "3.0.0"
    - "3.0.1"
    - "3.0.2"
    - "3.1.0"
---

# ODCS YAML

The Open Data Contract Standard (ODCS) defines a YAML format for **data contracts** — declarative specifications of a dataset's structure, semantics, quality, SLAs, infrastructure, ownership, and support channels. This skill teaches agents how to read, write, and reason about ODCS contracts at versions **3.0.0, 3.0.1, 3.0.2, and 3.1.0**.

## When to use this skill

Activate this skill when the user is doing any of:

- Writing a new ODCS contract from scratch.
- Reading an existing contract YAML and asking what fields mean.
- Validating a contract or debugging schema validation errors.
- Migrating a contract between ODCS versions (especially v2 → v3 or v3.0.x → v3.1.0).
- Asking about ODCS sections, fields, the object/property/element schema model, or how to model something specific (a Kafka topic, a partitioned table, a hierarchical document, …) as a contract.
- Asking what changed between ODCS versions, or which version to target.

Do **not** use this skill for the Python implementation of ODCS — that's covered by the `odcs-python` skill.

## How this fits with ODPS

ODCS and the **Open Data Product Standard (ODPS)** are sibling Bitol standards. The split:

- **ODCS (this skill)** describes a single dataset's *contract*: schema, quality, SLA, server bindings, ownership of one logical asset.
- **ODPS** describes a *data product* — a packaged unit with `inputPorts[]`, `outputPorts[]`, and `managementPorts[]`. Each port is a *named reference* to an ODCS contract via `contractId`. ODPS does not redefine schema, quality, or SLA — it bundles ODCS contracts and adds product-level metadata (team, support channels, lineage between input and output contracts).

If the user is asking "how do I describe one table / one stream / one document?", that's ODCS. If the user is asking "how do I describe a packaged set of inputs and outputs that my team owns and ships?", that's ODPS — covered by the `odps-yaml` skill if installed.

## Mental model

A data contract is **not** a database schema — it is a *logical* specification that ties a business view of data to one or more physical implementations. Three layers to keep straight:

1. **Fundamentals** — identity and metadata about *the contract itself*: who owns it, what version of the standard it conforms to (`apiVersion`), what version the contract is at (`version`), what status it's in (proposed/draft/active/deprecated/retired), what domain and data product it belongs to.
2. **Schema** — the dataset's structure, expressed in v3's terminology of **objects** (a structure of data — table, document, payload), **properties** (attributes of an object — column, field), and **elements** (either an object or a property). The schema can carry both a logical view (`logicalType`) and a physical view (`physicalType`, `physicalName`).
3. **Cross-cutting sections** — quality checks, SLAs, server/infrastructure references, support channels, team members, roles, pricing, custom extensions. Each describes a different facet of how the contract is used and operated.

The contract should be **platform agnostic**: the same logical schema can be backed by Postgres, Kafka, S3, BigQuery, etc. The `servers` section is where you bind it to physical infrastructure, not the schema.

> The provided JSON schemas are companions to the standards (ODCS or ODPS), it means that they do not define the standards and may include bugs. In case of conflict between the standard and the JSON Schema, the standard takes precedence.
> — [docs/v3.1.0/README.md](references/docs/v3.1.0/README.md)

## Top-level sections

A complete ODCS v3 contract is structured as follows. Each section has its own reference doc — link from the body to the file rather than restating the field tables.

| Section | Purpose | Reference |
|---|---|---|
| **Fundamentals** | Contract identity, version, status, domain, ownership metadata. The `apiVersion`, `kind`, `id`, `version`, and `status` fields are required. | [`docs/v3.1.0/fundamentals.md`](references/docs/v3.1.0/fundamentals.md) |
| **Schema** | The dataset structure: objects, properties, types, primary keys, partitioning, transformations. Supports tables, documents, hierarchies, and arrays. | [`docs/v3.1.0/schema.md`](references/docs/v3.1.0/schema.md) |
| **References** | Authoritative external definitions and links. | [`docs/v3.1.0/references.md`](references/docs/v3.1.0/references.md) |
| **Data Quality** | Quality checks, scheduling, library of common metrics (`rowCount`, `nullValues`, `invalidValues`, `duplicateValues`, `missingValues` since v3.1.0). | [`docs/v3.1.0/data-quality.md`](references/docs/v3.1.0/data-quality.md) |
| **Support & Communication Channels** | How consumers reach the data product team — Slack, email, ticketing, notifications. | [`docs/v3.1.0/support-communication-channels.md`](references/docs/v3.1.0/support-communication-channels.md) |
| **Pricing** | Cost model for consumers (introduced/expanded across v3.x). | [`docs/v3.1.0/pricing.md`](references/docs/v3.1.0/pricing.md) |
| **Team** | Members of the team owning the contract. | [`docs/v3.1.0/team.md`](references/docs/v3.1.0/team.md) |
| **Roles** | Access roles and the permissions/responsibilities they imply. | [`docs/v3.1.0/roles.md`](references/docs/v3.1.0/roles.md) |
| **Service Level Agreement** | Availability, freshness, latency, and other SLA properties. | [`docs/v3.1.0/service-level-agreement.md`](references/docs/v3.1.0/service-level-agreement.md) |
| **Infrastructure & Servers** | Physical bindings: types include `bigquery`, `postgresql`, `kafka`, `snowflake`, `s3`, `azure`, `sftp`, `databricks`, `hive`, `impala`, `duckdb`, `actianzen`, plus a generic `custom` type. | [`docs/v3.1.0/infrastructure-servers.md`](references/docs/v3.1.0/infrastructure-servers.md) |
| **Custom & Other Properties** | Extension mechanism for fields the standard doesn't cover. | [`docs/v3.1.0/custom-other-properties.md`](references/docs/v3.1.0/custom-other-properties.md) |

For the canonical TOC, see [`docs/v3.1.0/README.md`](references/docs/v3.1.0/README.md).

## The schema model in v3

This is the area users get wrong most often. ODCS v3 dropped the v2 "tables and columns" framing in favor of a more general structure:

- **Object** (`schema[*]` entry, `logicalType: object`) — a structure of data. A relational table, a NoSQL document, a Kafka message payload, an Avro record. Has a `name`, optional `physicalType` (e.g. `table`), `physicalName`, `description`, and a `properties` array.
- **Property** (`schema[*].properties[*]`) — an attribute of an object. A column in a table, a field in a payload. Has `name`, `logicalType` (one of `string`, `date`, `number`, `integer`, `object`, `array`, `boolean`, plus `timestamp` and `time` since v3.1.0), `physicalType`, plus flags like `primaryKey`, `required`, `unique`, `partitioned`, etc.
- **Element** — the umbrella term for either an object or a property. Used in cross-cutting features like SLAs (`slaProperties[].element`).

For nested data (arrays, structs):
- An `array` property uses `items` to describe the element type (which itself can be an object with nested `properties`).
- An `object` property can carry its own `properties` array for nested fields.

See the schema doc for full examples (complete schema, simple array, array of objects, object with object properties, primitive arrays). Examples in this skill that exercise the schema model:
- [`examples/table-column.odcs.yaml`](references/examples/table-column.odcs.yaml) — minimal valid contract with a single table, one property, and authoritative definitions.
- [`examples/kafka-schemaregistry.odcs.yaml`](references/examples/kafka-schemaregistry.odcs.yaml) — Kafka domain example (different physical binding, same schema model).
- [`examples/full-example.odcs.yaml`](references/examples/full-example.odcs.yaml) — comprehensive contract exercising every section.

## Versions and migrations

This skill targets four spec versions. Pick the version a contract declares in its `apiVersion` field (`v3.0.0`, `v3.0.1`, `v3.0.2`, or `v3.1.0`).

The full per-version change history is in [`CHANGELOG.md`](references/CHANGELOG.md). The headline differences:

### v3.1.0 — current (released 2025-12-08)
- **Modular docs**: the spec is now split into per-section docs instead of one monolithic file.
- **Relationships (foreign keys)** added to both `SchemaObject` and `SchemaProperty` (`relationships[]` field). Supports composite keys, schema-level and property-level relationships, dot-shorthand (`accounts.address_street`) and fully qualified (`/schema/.../properties/...`) references.
- **Logical types**: `timestamp` and `time` added to `logicalType`; new `timezone` and `defaultTimezone` options in `logicalTypeOptions`.
- **Quality**: standard library of metrics (`rowCount`, `nullValues`, `invalidValues`, `duplicateValues`, `missingValues`); explicit `schedule` and `scheduler` fields.
- **Team**: now an *object* (with `name`, `description`, `members`, `tags`, `customProperties`, `authoritativeDefinitions`) instead of an array. The v3.0.x array form is still accepted but **deprecated** and will be removed in v4.
- **`slaDefaultElement`** is deprecated, removal planned for v4 (RFC 21).
- **Breaking schema-only change**: `exclusiveMaximum`/`exclusiveMinimum` for numeric/date types are now numbers/strings (per JSON Schema spec), not booleans. Most authored contracts won't notice; tooling that emits the old boolean form will need updating.
- **Servers**: format/delimiter fields on Azure/S3/Sftp servers became free-form strings (no longer enums). New server types: `hive`, `impala`, `actianzen`. `duckdb` schema field is now a string.

### v3.0.2 — released 2025-03-31
- Adds `physicalName` for properties.
- Specifies `YYYY-MM-DDTHH:mm:ss.SSSZ` as default date format.
- Adds `name` and `description` to team members.
- Athena server: `staging_dir` → `stagingDir`.

### v3.0.1 — released 2024-12-22
- Adds `authoritativeDefinitions`, `description.customProperties`, `description.authoritativeDefinitions`, `role.customProperties` to the JSON schema.
- Updates `status` field examples and `tags`/`authoritativeDefinitions` descriptions.

### v3.0.0 — released 2024-10-21
- The big v2 → v3 break. Many fields renamed, the schema section restructured to support non-table formats.
- `uuid` → `id`, `quantumName` → `dataProduct` (now optional), `datasetDomain` → `domain`.
- Schema: `columns` → `properties`, `isNullable` → `required` (sense inverted), `isPrimaryKey` → `primaryKey`, `sampleValues` → `examples`, `dataGranularity` → `dataGranularityDescription`, `encryptedColumnName` → `encryptedName`, `partitionStatus` → `partitioned`, `criticalDataElementStatus` → `criticalDataElement`, `transformSourceTables` → `transformSourceObjects`.
- New sections: **Support & Communication Channels** and **Servers**.
- Many v2 fields dropped — credentials (`username`, `password`), source platform info, scheduler app name, etc. The reasoning: credentials should not be in a contract; platform/server info moved to the dedicated `servers` section.

## Common questions

**"What's the minimum valid ODCS contract?"**
Required fields are `apiVersion`, `kind: DataContract`, `id`, `version`, and `status`. See [`examples/table-column.odcs.yaml`](references/examples/table-column.odcs.yaml) for a near-minimal example that adds a name and a schema. The `name` field at the top level is *optional*, contrary to what users often assume.

**"Where does authentication / credentials go?"**
Nowhere in the contract. As of v3.0.0, credentials are explicitly excluded — the contract is meant to be safe to publish. Configure auth in your runtime/infrastructure layer.

**"How do I describe a Kafka topic / NoSQL document / nested JSON payload?"**
Use the `schema[*]` entries with `logicalType: object` and a `physicalType` matching your binding (e.g. `kafka`, `document`, `record`). Use nested `properties` with `logicalType: object` or `logicalType: array` + `items` for structure. See [`examples/kafka-schemaregistry.odcs.yaml`](references/examples/kafka-schemaregistry.odcs.yaml) and the "Simple Array" / "Array of Objects" examples in [`docs/v3.1.0/schema.md`](references/docs/v3.1.0/schema.md).

**"How do I express foreign keys?"**
Only in v3.1.0+. Use the `relationships[]` field on a `SchemaObject` (with explicit `from` and `to`) or on a `SchemaProperty` (where `from` is implicit). Composite keys use arrays. See the v3.1.0 changelog entry for the full grammar.

**"Which `apiVersion` should I declare?"**
Match the version of the standard your tooling validates against. If you're starting fresh, use `v3.1.0`. The schemas in [`references/schemas/`](references/schemas/) let you validate against any of the four supported versions.

**"How do I extend the standard with custom fields?"**
Use the `customProperties` mechanism, available at most levels (top-level, schema, property, role, etc.). See [`docs/v3.1.0/custom-other-properties.md`](references/docs/v3.1.0/custom-other-properties.md). Do *not* invent top-level fields — they will fail strict validation.

## Validating a generated contract

After generating or substantially editing an ODCS YAML for a user, **validate it before handing it back**. Don't return a contract you haven't checked. The skill does not bundle a validator — instead, use whatever is already on the user's system, in this order of preference:

### 1. `open-data-contract-standard` pip module (preferred when available)

The Bitol-maintained Pydantic implementation. Validation is implicit at construction — if `from_file` returns without raising, the contract is valid. This is the closest thing to authoritative validation and catches v2/v3 confusion and strict-mode violations (`extra='forbid'`).

```bash
python -c "from open_data_contract_standard.model import OpenDataContractStandard; OpenDataContractStandard.from_file('contract.odcs.yaml')"
```

If the import fails (`ModuleNotFoundError`), try installing with `pip install open-data-contract-standard` or `uv add open-data-contract-standard`, or fall through to option 2. Pin to the right module version for the target spec version (see the `odcs-python` skill if installed, or the upstream README).

### 2. `datacontract-cli` (if installed)

The third-party [Data Contract CLI](https://github.com/datacontract/datacontract-cli) consumes ODCS and exposes a user-friendly `lint` command. Not a Bitol project — a downstream consumer — so it may lag the latest spec, but it's widely installed.

```bash
datacontract lint contract.odcs.yaml
```

Exit 0 means valid. If `datacontract` is not on `PATH`, fall through to option 3.

### 3. JSON Schema validation against the vendored schema (always available)

The self-contained fallback. Each supported spec version has its JSON Schema vendored under [`references/schemas/`](references/schemas/). Pick the file matching the contract's `apiVersion`: `v3.0.0` → `odcs-json-schema-v3.0.0.json`, `v3.1.0` → `odcs-json-schema-v3.1.0.json`, and so on.

```bash
python -c "import json, yaml, jsonschema; jsonschema.validate(yaml.safe_load(open('contract.odcs.yaml')), json.load(open('references/schemas/odcs-json-schema-v3.1.0.json')))"
```

Requires `pyyaml` and `jsonschema` (both small, stdlib-adjacent). **Caveat**: the JSON Schema is a *companion* to the spec, not authoritative — see the Pitfalls entry on treating it as truth. A contract that passes this check may still violate the prose spec in edge cases, and vice versa. When option 1 or 2 is available, prefer it.

### Reporting results

If validation fails, read the error, map it back to the YAML, and either fix it and re-validate or surface the exact problem to the user. Don't silently return an invalid contract with a note — fix it first.

## Pitfalls

- **Confusing v2 and v3 field names.** Tooling and examples on the internet often predate v3.0.0. If you see `columns`, `isPrimaryKey`, `isNullable`, `quantumName`, `datasetDomain`, `uuid`, `sampleValues`, `clusterStatus`, `transformSourceTables`, etc. — that's v2. The user is either reading legacy docs or has a contract that needs migrating.
- **Setting `required: false` thinking it means "primary key not required".** The `required` field is the *inverse* of v2's `isNullable`. `required: true` means the field cannot be null.
- **Expecting `name` to be required at the top level.** It is not. `id` is the unique identifier.
- **Vendoring or pasting fields from one version's schema into a contract declaring a different `apiVersion`.** The validator will reject mismatched fields. When in doubt, validate against the matching schema in [`references/schemas/`](references/schemas/).
- **Strict additional-properties checks in v3.1.0.** Several sections (`authoritativeDefinitions`, `customProperties`, `dataQuality`, `dataQualityCheck`, `price`, `role`, `schemaElement`, `server`, `slaProperties`, `support`, `team`) reject unknown fields in v3.1.0's strict mode. Use `customProperties` for extensions instead of adding new keys directly.
- **Treating the JSON Schema as authoritative.** It is not — the textual spec docs are. The JSON Schema is a companion that may have bugs. When the schema and the docs disagree, the docs win.
- **Using the deprecated team-as-array form in new contracts.** v3.1.0 still accepts it, but it is removed in v4. Use the team-as-object form for any contract written today.
- **Generating a contract without validating it.** Agents routinely hand back YAML they never checked. Don't. Use the "Validating a generated contract" section above before returning a contract to the user.

## Reference index

Everything below lives in this skill's `references/` directory:

- **Schemas** (one per supported version): [`schemas/`](references/schemas/)
  - `odcs-json-schema-v3.0.0.json`
  - `odcs-json-schema-v3.0.1.json`
  - `odcs-json-schema-v3.0.2.json`
  - `odcs-json-schema-v3.1.0.json`
- **Prose docs** (v3.1.0): [`docs/v3.1.0/`](references/docs/v3.1.0/) — README, fundamentals, schema, data-quality, service-level-agreement, infrastructure-servers, support-communication-channels, roles, team, references, pricing, custom-other-properties.
- **Examples**: [`examples/`](references/examples/) — `table-column.odcs.yaml`, `kafka-schemaregistry.odcs.yaml`, `full-example.odcs.yaml`.
- **Changelog**: [`CHANGELOG.md`](references/CHANGELOG.md).

When answering a question, prefer linking the user to the relevant reference file rather than paraphrasing the spec — they get to see the canonical source.
