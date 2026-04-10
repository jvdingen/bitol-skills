# Skill Playbook

The reusable workflow for building or updating any skill in `bitol-skills`. Read
this **before** touching `skills/`. CLAUDE.md gives the rules; this file gives
the order of operations.

If you find yourself improvising a step that isn't in this playbook, stop —
either the playbook is wrong (fix it) or you're about to do something the repo
doesn't endorse.

---

## When to use this playbook

| Situation | Section |
|-----------|---------|
| Creating a brand-new skill | [Creating a skill](#creating-a-skill) (steps 1–11) |
| Upstream spec released a new version | [Updating a skill](#updating-a-skill-when-upstream-changes) |
| Fixing a typo or wording in an existing skill body | Just edit `SKILL.md` → step 8 (validate) → commit |
| Adding a new example to an existing skill | Add to `references/examples/`, run validate + tests, commit |

---

## Creating a skill

The workflow is 11 numbered steps. Do them in order. Each step has a clear
"done" state — don't skip ahead.

### 1. Scope the skill

**Goal**: decide what one concern this skill addresses, before writing
anything.

- One skill = one concern. If you're tempted to cover two, split them.
  (`odcs-yaml` covers the YAML structure and semantics. `odcs-python` covers
  the Python lib. They are independent installs.)
- Decide which spec versions are in scope. List them explicitly.
- **Skills are independently installable.** Do not assume any other skill is
  also present on the user's system. Some duplication between related skills
  is acceptable when each must stand alone.

**Output**: a one-paragraph scope statement you can paste into the SKILL.md
description and `metadata.spec_versions`. Write it in your head or in a
scratch buffer — not yet committed anywhere.

### 2. Inventory upstream sources

**Goal**: know exactly which upstream files this skill will vendor, before
fetching anything.

- Identify the upstream repo(s) for the spec/library this skill teaches.
  Cross-reference [`REFERENCES.md`](REFERENCES.md) for the canonical URLs.
- Pin to **tags, not branches**. Vendoring from a branch is non-reproducible.
- Prefer one version's complete doc set over partial slices of many versions,
  unless the skill explicitly supports multiple versions (in which case vendor
  each version's schema separately and one version's full prose docs as the
  reference baseline).
- Look for: JSON Schema(s), spec markdown docs, representative example
  files, CHANGELOG / migration guides, version-mapping tables.
- Use `gh api` to browse the upstream tree and find paths. Example:
  ```bash
  gh api repos/bitol-io/open-data-contract-standard/contents/schema?ref=v3.1.0
  gh api repos/bitol-io/open-data-contract-standard/contents/docs?ref=v3.1.0
  ```

**Output**: a list of `(repo, ref, src_path, dest_path)` tuples in your head
or in a scratch buffer. You'll commit them in step 3.

### 3. Draft `sources.toml`

**Goal**: encode the inventory from step 2 into a machine-readable manifest
that `sync_specs.py` consumes.

Create `skills/<skill-name>/sources.toml`:

```toml
# Machine-readable vendoring manifest. Consumed by scripts/sync_specs.py.
# One [[source]] entry per file. NEVER hand-edit files inside references/ —
# they are overwritten by sync.

[[source]]
repo = "bitol-io/open-data-contract-standard"
ref  = "v3.1.0"
src  = "schema/odcs-json-schema-v3.1.0.json"
dest = "references/schemas/odcs-json-schema-v3.1.0.json"

[[source]]
repo = "bitol-io/open-data-contract-standard"
ref  = "v3.1.0"
src  = "docs/fundamentals.md"
dest = "references/docs/v3.1.0/fundamentals.md"

# ... one entry per vendored file
```

Conventions:

- One `[[source]]` per file. No globs (explicit > implicit; future drift is
  easier to read in diffs when paths are listed).
- The same skill may pull from multiple repos and refs.
- `dest` paths should mirror upstream structure inside `references/`, with a
  version segment (`references/schemas/...-v3.1.0.json` or
  `references/docs/v3.1.0/...`) so multi-version skills don't collide.

### 4. Vendor with `sync_specs.py`

**Goal**: write the upstream files into `references/` reproducibly.

```bash
uv run scripts/sync_specs.py skills/<skill-name>          # plan only (default)
uv run scripts/sync_specs.py skills/<skill-name> --apply  # write files
```

After `--apply`, `references/` should contain every file declared in
`sources.toml`. **Do not hand-edit any file under `references/`** — the next
sync will overwrite your changes. Annotations and explanations belong in
`SKILL.md`, not in vendored files.

### 5. Write `SKILL.md` frontmatter

**Goal**: a frontmatter block that passes `validate_skill.py`.

Create `skills/<skill-name>/SKILL.md` starting with:

```markdown
---
name: <skill-name>
description: <≤1024 chars: what + when + versions>
metadata:
  spec_versions:
    - "3.0.0"
    - "3.0.1"
    - "3.0.2"
    - "3.1.0"
---
```

Frontmatter rules (validator-enforced):

| Field | Rule |
|---|---|
| `name` | **Must equal the parent directory name.** 1–64 chars, `[a-z0-9-]` only, no leading/trailing/consecutive hyphens. |
| `description` | 1–1024 chars. Lead with what the skill does, then trigger keywords ("Use when the user asks about ODCS, data contracts, contract YAML, ..."), then versions in scope. The agent uses this to decide whether to invoke the skill — be specific. |
| `metadata.spec_versions` | List of `"X.Y.Z"` strings. This is the machine-readable source of truth for which versions the skill supports. Mirror it in the description prose so it surfaces at discovery time. |
| `compatibility` (optional) | Only if the skill has real environment requirements. e.g. `odcs-python` declares `Requires Python 3.10+ and the open-data-contract-standard PyPI package`. Most skills should omit this. |
| `license` (optional) | Defaults to repo license; only set explicitly if different. |
| `allowed-tools` (optional) | Experimental and CLI-only — only set if you have a strong reason. |

**Anti-pattern**: trying to make the description shorter by dropping the
trigger keywords. The keywords are what makes the skill discoverable. Keep
them, even if it means rewording elsewhere.

### 6. Write the meaning layer (`SKILL.md` body)

**Goal**: human-written prose that gives an agent enough context to reason
about the spec, grounded in the vendored references.

Length: **under 500 lines / 5000 tokens**. The body is loaded in full when
the skill is activated. Push detail into the vendored references and link to
them from the body — don't paste schema content inline.

Recommended sections (adapt as the skill demands):

1. **When to use this skill** — concrete trigger examples ("if the user is
   writing an ODCS contract YAML", "if the user is debugging schema
   validation errors", ...).
2. **Mental model** — how to *think* about the spec. Not what fields exist
   (the schema covers that), but the concepts the spec encodes and the
   relationships between them.
3. **Major sections** — a high-level pass over the spec's structure, with
   inline links to the relevant vendored doc files (`See
   [fundamentals](references/docs/v3.1.0/fundamentals.md)`).
4. **Versions and migrations** — what changed between supported versions,
   what to watch out for when upgrading. Reference the vendored CHANGELOG.
5. **Common questions and answers** — anticipate the questions agents will
   field. Either answer them inline or point to the right reference file.
6. **Pitfalls** — what bites people. Strict mode? Required fields people
   forget? Validator quirks?

**The grounding rule**: every semantic claim in the body must be traceable
to a vendored file. If you can't point to a reference, the claim does not
belong in the skill. Inventing semantics — even plausible-sounding ones —
poisons the skill for users who trust it.

**Cross-link sparingly**: file references in `SKILL.md` should be one level
deep from the skill root (e.g., `references/foo.md`). No nested chains.

### 7. Add focused examples

**Goal**: 2–5 representative examples that *teach*, not an exhaustive mirror
of every example upstream offers.

- Pick examples that span the range: minimal-valid → idiomatic → full /
  comprehensive.
- Vendor them through `sources.toml` like everything else, not by hand.
- If the example is something only this skill needs (not present upstream),
  put it in `assets/` instead of `references/` and write it directly. Mark
  it as locally authored in a comment.

### 8. Validate

```bash
uv run scripts/validate_skill.py skills/<skill-name>
```

Must pass cleanly. The validator checks:

- All frontmatter rules from step 5
- `name` matches parent directory
- `metadata.spec_versions` present and well-formed (`^\d+\.\d+\.\d+$`)
- `references/` (plural — never `reference/`) exists if any vendored
  material is present
- SKILL.md body length warning (>500 lines is a warning, not a failure)

Fix every issue before moving on. Don't suppress warnings unless you have a
documented reason.

### 9. Test

**Goal**: at least one automated check that catches drift between vendored
material and the skill's claims.

Add a test in `tests/test_<skill-name>.py` that:

- Loads each vendored example through the relevant validator (the JSON
  schema for YAML skills, the Python lib for `odcs-python`).
- Asserts every example parses and validates clean.
- Asserts `metadata.spec_versions` matches the schemas actually present in
  `references/`.

This catches the common drift mode where a sync updates a schema but breaks
an example. Run:

```bash
uv run pytest tests/test_<skill-name>.py
```

### 10. Update README

Add a row to the install table in `README.md`:

| Skill | What it covers | Install |
|---|---|---|
| `<skill-name>` | One-line summary | `cp -r skills/<skill-name> ~/.claude/skills/` |

Keep it terse — README is for users deciding which skill to install, not for
deep documentation.

### 11. Commit (single, self-consistent commit)

Vendored material, `SKILL.md`, `sources.toml`, examples, tests, and the
README update **all go in one commit** so the skill is internally consistent
at every git revision. A user checking out any commit should get a
working, validating skill — never a half-finished one.

Commit message format:
```
add <skill-name> skill (covers <spec> v<X.Y.Z>...)
```

---

## Updating a skill when upstream changes

The drift workflow. Use when an upstream spec releases a new version, fixes
a typo in their schema, etc.

### 1. Detect drift

```bash
uv run scripts/sync_specs.py skills/<skill-name>
```

(No `--apply`.) Reads `sources.toml`, fetches the current upstream content
at each pinned ref, and reports what would change. If nothing has drifted,
stop — there's nothing to do.

### 2. Classify the change

Read the diff. Decide:

- **Mechanical**: schema field added, doc typo fixed, example reformatted.
  No semantic change. The body of `SKILL.md` may not need any edits.
- **Semantic**: a field's meaning changed, a section was reorganized, a
  default behavior shifted, a new concept was added. The body of `SKILL.md`
  almost certainly needs edits.

When in doubt, treat it as semantic and re-read the meaning layer with the
new vendored content open.

### 3. Apply

```bash
uv run scripts/sync_specs.py skills/<skill-name> --apply
```

### 4. Update the meaning layer

If the change was semantic, edit `SKILL.md` body. Trace every semantic claim
back to the new vendored content — claims that no longer have a reference
are dead and must be removed or rewritten.

### 5. Bump versions if a new spec version is now supported

If the upstream change is a new spec version that the skill now supports:

- Append the version to `metadata.spec_versions`.
- Mention it in the description prose.
- Add a `[[source]]` entry to `sources.toml` for the new version's schema
  (and any other version-specific files).
- Re-run `sync_specs.py --apply` to vendor the new files.

**Never silently bump.** A version bump is the *result* of validating the
skill against the new version, not the trigger.

### 6. Validate, test, commit

```bash
uv run scripts/validate_skill.py skills/<skill-name>
uv run pytest tests/test_<skill-name>.py
```

Both must pass. Commit `references/` changes and `SKILL.md` changes
together.

---

## Cheatsheet — commands you'll actually run

```bash
# Setup (once)
uv sync

# Vendor inventory for a skill
gh api repos/<owner>/<repo>/contents/<path>?ref=<tag>

# Sync workflow
uv run scripts/sync_specs.py skills/<name>          # plan
uv run scripts/sync_specs.py skills/<name> --apply  # write
uv run scripts/sync_specs.py skills                 # all skills, plan
uv run scripts/sync_specs.py skills --apply         # all skills, write

# Validate
uv run scripts/validate_skill.py skills/<name>      # one skill
uv run scripts/validate_skill.py skills             # all skills

# Test
uv run pytest                                       # all
uv run pytest tests/test_<name>.py                  # one skill's tests
```

---

## Anti-patterns specific to this playbook

- **Skipping `sources.toml` and vendoring by hand once the tooling exists.**
  The tooling exists so vendoring is reproducible. Hand-vendoring breaks the
  drift workflow.
- **Editing files inside `references/`.** They are overwritten by sync.
  Annotations belong in `SKILL.md`.
- **Pasting schema content into the SKILL.md body.** The body is the meaning
  layer. Schemas live in `references/`. Link, don't paste.
- **Inventing semantics** ("I'm pretty sure this field means X"). If you
  can't point to a vendored file that supports the claim, it does not
  belong in the skill.
- **Bumping `spec_versions` before validating** the skill against the new
  version. The bump is the certification, not the trigger.
- **Splitting a skill update across multiple commits** ("I'll fix the body
  in the next PR"). Every commit must leave the skill internally
  consistent.
- **Assuming another skill is installed.** Each skill must be useful
  standalone, even if it duplicates content from a related skill.
