# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of **Agent Skills** that teach AI agents about the [Bitol](https://bitol.io/) data
standards — primarily **ODCS** (Open Data Contract Standard) and **ODPS** (Open Data Product
Standard). Skills are authored to the canonical [agentskills.io specification](https://agentskills.io/specification)
so they are portable across Claude Code, the Claude Agent SDK, and any other framework that
consumes the format. End users install skills manually by copying the relevant `skills/<name>/`
folder into their own `~/.claude/skills/` directory.

The repo's job is to keep these skills **accurate, current, and self-contained** as upstream
specs evolve.

## Repository layout

```
skills/                    # one folder per skill — each is independently installable
  <skill-name>/
    SKILL.md               # frontmatter + body (the meaning layer)
    references/            # vendored upstream material (the mechanical truth)
    scripts/               # optional, if the skill ships executable helpers
    assets/                # optional, templates / examples / data files
scripts/                   # repo tooling, NOT skill scripts
  sync_specs.py            # diff vendored references against upstream
  validate_skill.py        # lint a skill against the agentskills.io spec
tests/                     # pytest — covers tooling and validates example fixtures
REFERENCES.md              # canonical upstream URLs (read this first)
pyproject.toml + uv.lock   # uv-managed Python tooling
```

`REFERENCES.md` is the single source of truth for upstream URLs. Read it before reaching for
any Bitol or Agent SDK link in your head — those may be stale.

## Skill authoring rules

These encode the [agentskills.io spec](https://agentskills.io/specification) — violations will
fail `validate_skill.py`. **Before creating or updating any skill, read [`SKILL_PLAYBOOK.md`](SKILL_PLAYBOOK.md)**
for the step-by-step workflow.

- **Directory == name**: `skills/<name>/SKILL.md` must declare `name: <name>`. The two must
  match exactly. The `name` field allows only `[a-z0-9-]`, max 64 chars, no leading/trailing/
  consecutive hyphens.
- **Description**: max 1024 chars. Lead with what the skill does, then the trigger keywords
  ("Use when the user asks about ODCS YAML, data contracts, ..."). The description is what the
  agent uses to decide when to invoke the skill — make it specific.
- **Body length**: keep `SKILL.md` under ~500 lines / ~5000 tokens. Push detail into
  `references/` files and link to them. The body is loaded in full once activated; references
  are loaded on demand.
- **`references/` is plural** (per spec). Not `reference/`.
- **File references one level deep** from `SKILL.md`. No nested chains.
- **Spec version targets** live in frontmatter `metadata.spec_versions` as a list of strings,
  e.g. `["3.0.0", "3.0.1", "3.0.2"]`. This is machine-readable so `validate_skill.py` can
  check it. The same versions should also appear in the `description` so the agent surfaces
  them at discovery time.
- Use `compatibility` only when a skill genuinely needs it (e.g. the `odcs-python` skill should
  declare its Python version requirement). Most skills do not need this field.

## Content model: vendored truth + hand-written meaning

Every skill has two layers, and edits should respect the split:

1. **`references/` — the mechanical truth.** Vendored from upstream Bitol repos: JSON Schemas,
   spec markdown, example contracts/products. This is what makes claims *verifiable*. Never
   hand-edit vendored files; they are overwritten by `sync_specs.py`. If you need to annotate,
   put the annotation in `SKILL.md`.
2. **`SKILL.md` body — the meaning layer.** Human-written prose explaining how to *think*
   about the spec: when each construct applies, common pitfalls, idiomatic patterns, how to
   answer typical questions. Every semantic claim here should be traceable to something in
   `references/`.

If you're tempted to write semantic guidance in a vendored file, or to paste raw schema chunks
into the body, you're fighting the model — stop and reconsider.

## Current spec version targets

| Skill area | Versions in scope |
|------------|-------------------|
| ODCS       | 3.0.0 and above   |
| ODPS       | 1.0.0             |

When a new upstream version is released, **append** it to the relevant skill's
`metadata.spec_versions` after running the drift workflow below. Do not silently bump — the
bump is the *result* of validating the skill against the new version, not the trigger.

## Tooling commands

```bash
uv sync                                            # install Python deps
uv run pytest                                      # run all tests
uv run scripts/sync_specs.py                       # diff vendored refs vs upstream, print report
uv run scripts/sync_specs.py --apply               # write upstream changes into references/
uv run scripts/validate_skill.py skills/<name>     # lint a single skill
uv run scripts/validate_skill.py skills            # lint all skills
```

## Drift workflow (when upstream changes)

1. `uv run scripts/sync_specs.py` — see what drifted.
2. Review the diff. Decide whether the change is mechanical (schema field added) or semantic
   (the *meaning* of a construct changed).
3. `uv run scripts/sync_specs.py --apply` to update `references/`.
4. If semantics changed, update the affected `SKILL.md` body. If only mechanics changed, the
   body may not need edits — but check.
5. Append the new version to `metadata.spec_versions` (and the `description`).
6. `uv run scripts/validate_skill.py skills/<name> && uv run pytest`.
7. Commit `references/` changes and `SKILL.md` changes in the same commit so the skill stays
   internally consistent at every revision.

## Anti-patterns — do not do these

- **Do not have skills fetch from upstream at runtime.** Skills must be self-contained once
  installed. All spec material is vendored.
- **Do not exceed the 500-line SKILL.md guideline.** Split into `references/` files.
- **Do not invent ODCS/ODPS semantics.** Every claim in a skill body must be grounded in
  vendored material. If you cannot point to a reference file that supports a claim, the claim
  does not belong in the skill.
- **Do not hand-edit files inside `references/`.** They are overwritten by sync. Annotate in
  the body instead.
- **Do not add tooling beyond sync + validate + test** unless there is a concrete need. This
  repo deliberately keeps the tooling layer thin.
- **Do not use `reference/` (singular).** The spec mandates plural; the validator enforces it.

## Current state

This repo is being bootstrapped. As of this writing, `REFERENCES.md` and `CLAUDE.md` exist,
but `skills/`, `scripts/`, `tests/`, and `pyproject.toml` are not yet created. When picking up
work, check what exists before assuming any of the above is in place.
