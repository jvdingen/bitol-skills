---
name: odps-yaml
description: Open Data Product Standard (ODPS) reference for the YAML data product format. Covers structure, semantics, the data-product mental model (input ports, output ports, management ports, contract references), top-level sections (fundamentals, product information, management ports, support, team, ancillary objects), and the relationship between ODPS data products and ODCS data contracts. Use when the user is writing, reading, validating, or debugging an ODPS data product YAML; asks about ODPS fields or sections; needs to understand how data products differ from data contracts; or is wiring an ODPS product to one or more ODCS contracts. Supports ODPS spec version 1.0.0. Vendored references include the v1.0.0 JSON Schema, the full v1.0.0 prose spec, the CHANGELOG, and two representative example products.
metadata:
  spec_versions:
    - "1.0.0"
---

# ODPS YAML

The Open Data Product Standard (ODPS) defines a YAML format for **data products** — packaged, versioned units of data that an organization treats as a product, with declared inputs, outputs, management interfaces, ownership, and support channels. This skill teaches agents how to read, write, and reason about ODPS products at version **1.0.0** (released 2025-09-24, marked APPROVED).

## When to use this skill

Activate this skill when the user is doing any of:

- Writing a new ODPS data product YAML from scratch.
- Reading an existing data product YAML and asking what fields mean.
- Validating a product or debugging schema validation errors.
- Wiring a data product to one or more ODCS data contracts (the `contractId` linkage on ports).
- Asking what an "input port", "output port", or "management port" means in ODPS terms.
- Asking how ODPS relates to ODCS — when to reach for which standard.
- Asking what changed between ODPS versions (v0.9.0 → v1.0.0).

Do **not** use this skill for the data *contract* layer — that's `odcs-yaml`. ODPS describes the *product* (the packaging, the ports, the team); ODCS describes the *contract* on each port (the schema, the quality, the SLA on a specific dataset).

## Mental model

A **data product** is the unit of ownership and consumption. It declares:

1. **Identity** — `id`, `name`, `version`, `status`, `domain`, `tenant`, plus a `description` block with `purpose`, `limitations`, and `usage`.
2. **Ports** — the *interfaces* of the product:
   - **Input ports** are the *expectations*: data the product needs to do its job. Each input port points at a data contract (`contractId`) the product expects upstream.
   - **Output ports** are the *promises*: data the product offers to consumers. Each output port points at a data contract (`contractId`) describing what the product guarantees to emit.
   - **Management ports** are the *control plane*: endpoints for discovering, observing, or controlling the product (e.g. a Kafka topic for dictionary updates, a REST endpoint for metrics).
3. **Operational metadata** — `support` (channels for consumers to reach the team), `team` (members owning the product), `customProperties`/`authoritativeDefinitions`/`tags` (extension and provenance hooks).

The split that matters: **ODPS does not describe schema, quality, or SLA**. Those live in the ODCS contracts that ports reference via `contractId`. A data product is a *thin* wrapper that bundles contracts together with team/support/management metadata.

> The combination of the name and version is the key. A new (major) version would be a new output port, for simplicity.
> — [docs/v1.0.0/README.md](references/docs/v1.0.0/README.md)

This is the ODPS versioning convention for ports: bumping a port's `version` while keeping its `name` produces a *separate* listed instance — both versions can coexist on the product so that consumers can migrate gradually.

## Top-level sections

A complete ODPS v1.0.0 product is structured as follows. The full per-section field tables live in the vendored spec at [`docs/v1.0.0/README.md`](references/docs/v1.0.0/README.md) — link there rather than restating tables.

| Section | Purpose | Required? |
|---|---|---|
| **Fundamentals** | Identity (`id`, `name`, `version`, `status`, `domain`, `tenant`), `description` block (`purpose`/`limitations`/`usage`), `tags`, `apiVersion`, `kind`. The required fields per the v1.0.0 schema are `apiVersion`, `kind`, `id`, and `status`. | Required: `apiVersion`, `kind`, `id`, `status` |
| **Product information** | `inputPorts[]` and `outputPorts[]` — the data interfaces. Output ports are required (a product without output is useless); input ports are optional (a pure-source product may have none). Each port has at least `name`, plus optional `version`, `contractId`, `type`, `description`, `tags`, `customProperties`, `authoritativeDefinitions`. Output ports can additionally carry `sbom` and `inputContracts` for provenance. | `outputPorts` recommended |
| **Management Ports** | `managementPorts[]` — control-plane endpoints. Each has a `name`, a `content` (`discoverability` / `observability` / `control`), an optional `type` (`rest` or `topic`, default `rest`), and an `url` or `channel`. | Optional |
| **Support & Communication Channels** | `support[]` — how consumers reach the team. Each entry has a `channel`, `url`, optional `tool` (`email`/`slack`/`teams`/`discord`/`ticket`/`other`), `scope` (`interactive`/`announcements`/`issues`), `description`, `invitationUrl`. Shared structure across all Bitol standards. | Optional |
| **Team** | `team` — object describing the team that owns the product, with `name`, `description`, `members[]`, `tags`, `customProperties`, `authoritativeDefinitions`. Aligned with ODCS v3.1.0's team-as-object form (RFC 0016). | Optional |
| **Ancillary Objects** | `customProperties[]` (key/value extension hook) and `authoritativeDefinitions[]` (typed links to external authoritative sources, e.g. `businessDefinition`, `tutorial`, `implementation`, plus `canonicalUrl` at the root level). | Optional |
| **Other Properties** | `productCreatedTs` — ISO-8601 UTC timestamp of when the product was created. | Optional |

For the canonical TOC, see [`docs/v1.0.0/README.md`](references/docs/v1.0.0/README.md).

## Ports in detail

This is the area users get wrong most often: ODPS ports are **references**, not definitions.

### Input ports — expectations

```yaml
inputPorts:
- name: payments
  version: 1.0.0
  contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db
- name: payments
  version: 2.0.0
  contractId: dbb7b1eb-7628-436e-8914-2a00638ba6da
```

Two listings of `payments` with different versions are **two separate ports** by the (name, version) key. Both can be live during a migration window. The `contractId` on each points at an ODCS contract that defines what the product expects to receive.

### Output ports — promises

```yaml
outputPorts:
- name: rawtransactions
  description: "Raw Transactions"
  type: tables
  version: 2.0.0
  contractId: c2798941-1b7e-4b03-9e0d-955b1a872b33
  sbom:
  - type: "external"
    url: "https://mysbomserver/mysbom"
  inputContracts:
  - id: dbb7b1eb-7628-436e-8914-2a00638ba6db
    version: 2.0.0
```

Output ports can carry **provenance** that input ports cannot:
- `sbom[]` — a software bill of materials. Each entry is an object with `url` (required) and `type` (default `"external"`), not a plain string.
- `inputContracts[]` — the *specific* upstream contracts this output was built from. This is how lineage gets captured at the contract level. Each entry accepts either `id` or `contractId` to reference the upstream contract (both are valid).

The `type` field on an output port (`tables`, etc.) is a free-form hint at the *kind* of port surface — it is not enumerated in v1.0.0.

### Management ports — control plane

```yaml
managementPorts:
- content: dictionary
  type: topic
  name: tpc-dict-update
  description: Kafka topic for dictionary updates
```

Management ports describe how operators *interact* with the product, separate from data flow. Three `content` categories: **discoverability** (catalog/dictionary endpoints), **observability** (metrics/logs/traces), **control** (start/stop/refresh actions). Type is `rest` (default) or `topic`.

See [`examples/customer-data-product.odps.yaml`](references/examples/customer-data-product.odps.yaml) for a comprehensive product exercising all three port types, and [`examples/simple-data-product.odps.yaml`](references/examples/simple-data-product.odps.yaml) for the minimum-viable shape.

## Versions and migrations

This skill targets ODPS v1.0.0 only. The full per-version history is in [`CHANGELOG.md`](references/CHANGELOG.md).

### v1.0.0 — current (released 2025-09-24, APPROVED)

- Adds `customProperties`, `tags`, and `authoritativeDefinitions` for `outputPorts` and `inputPorts` at the top level.
- **Team structure aligned on ODCS v3.1.0** — the team is now an object with `name`, `description`, `members`, `tags`, `customProperties`, `authoritativeDefinitions` (matching the ODCS v3.1.0 form per RFC 0016).
- `authoritativeDefinitions.type` changed from a closed enum to a recommended-values list, aligning with ODCS v3.1.0 (so types like `businessDefinition`, `tutorial`, `videoTutorial`, `transformationImplementation`, `implementation` are recommended but not the exhaustive set).
- Documentation expanded with additional keys.

### v0.9.0 — DEPRECATED (released 2025-07-15)

The first publicly approved release; structurally close to v1.0.0 but missing the port-level extension hooks and the ODCS-v3.1.0 team alignment. Not in scope for this skill — migrate to v1.0.0.

## Common questions

**"What's the minimum valid ODPS data product?"**
The required fields per the v1.0.0 schema are `apiVersion`, `kind: DataProduct`, `id`, and `status`. A typical minimal product also adds a `name` and at least one `outputPorts[]` entry. See [`examples/simple-data-product.odps.yaml`](references/examples/simple-data-product.odps.yaml) for a small example with one input port and one output port.

**"How does ODPS relate to ODCS?"**
ODPS describes the *product* — the packaging, ownership, and the set of ports it exposes. ODCS describes the *contract* on each port — the schema, the quality rules, the SLA, the server bindings for one specific dataset. A typical data platform has many ODCS contracts grouped into fewer ODPS products, with the linkage made via `contractId` on each port.

**"Where does the schema / data quality / SLA go?"**
Not in the ODPS file. Those live in the ODCS contracts the ports reference. ODPS is deliberately thin: it bundles contracts and adds product-level metadata.

**"How do I express that an output port was built from specific input contracts?"**
Use `outputPorts[].inputContracts[]` — a list of `{id, version}` pairs identifying upstream contracts. This is the v1.0.0 lineage hook.

**"What `type` values are allowed on output ports?"**
The v1.0.0 spec does not enumerate them — `type` is a free-form hint at the surface kind (e.g. `tables`, `topic`, `file`). Pick something descriptive.

**"What `content` values are allowed on management ports?"**
Three: `discoverability`, `observability`, `control`. The `type` is `rest` (default) or `topic`.

**"How do I extend the standard with custom fields?"**
Use the `customProperties[]` mechanism, available at the top level, on input/output ports (since v1.0.0), on management ports, on support entries, on team, and inside team members. Each entry is `{property, value, description}`. Do *not* invent top-level fields — strict validators will reject them.

**"Can a data product have only input ports, or only output ports?"**
The v1.0.0 spec marks `outputPorts` as the meaningful one ("a data product without output is useless"). Input ports are optional. A product can have outputs without inputs (a pure-source product).

## Pitfalls

- **Confusing ODPS with ODCS.** If the user is talking about columns, schema validation, primary keys, partitioning, server bindings, or quality checks — they want ODCS, not ODPS. ODPS only references those via `contractId`.
- **Treating ports as schema definitions.** A port is a *named reference* to a contract, not the contract itself. Defining schema fields directly inside an `outputPort` is wrong — put them in the linked ODCS contract.
- **Forgetting the (name, version) key for ports.** Two `inputPorts` entries with the same `name` but different `version` are two ports, not a duplicate. This is intentional — it lets producers run multiple versions during migration.
- **Vendored examples declare `apiVersion: v0.9.0`.** Both example files in `docs/examples/` (vendored at [`examples/simple-data-product.odps.yaml`](references/examples/simple-data-product.odps.yaml) and [`examples/customer-data-product.odps.yaml`](references/examples/customer-data-product.odps.yaml)) declare `apiVersion: v0.9.0` even though they're tagged in the v1.0.0 release. New products should use `apiVersion: v1.0.0` — the examples are slightly stale and should not be copied verbatim for the version field.
- **Treating the JSON Schema as authoritative.** As with ODCS, the JSON Schema is a companion to the prose spec, not the source of truth. When the schema and the docs disagree, the docs win.
- **Pre-v1.0.0 team-as-array form.** Any product that declares `team` as an array is using the deprecated v0.9.0 form. v1.0.0 aligned the team structure with ODCS v3.1.0's team-as-object — use that form for new products.
- **Adding free-form keys for things that have `customProperties`.** Top-level extension keys will fail strict validation. Use `customProperties[]` at the appropriate level (top, port, member, etc.) instead.

## Reference index

Everything below lives in this skill's `references/` directory:

- **Schema**: [`schemas/odps-json-schema-v1.0.0.json`](references/schemas/odps-json-schema-v1.0.0.json)
- **Prose spec** (v1.0.0): [`docs/v1.0.0/README.md`](references/docs/v1.0.0/README.md) — single-file spec covering Fundamentals, Product Information, Management Ports, Support & Communication Channels, Team, Ancillary Objects (Custom Properties / Authoritative Definitions), and Other Properties.
- **Examples**: [`examples/`](references/examples/) — `simple-data-product.odps.yaml` (minimal one-input-one-output product), `customer-data-product.odps.yaml` (comprehensive product with multiple input/output ports, management ports, SBOM, input contract lineage, support, and team).
- **Changelog**: [`CHANGELOG.md`](references/CHANGELOG.md).

When answering a question, prefer linking the user to the relevant reference file rather than paraphrasing the spec — they get to see the canonical source.
