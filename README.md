# bitol-skills

Agent Skills that teach AI agents about the [Bitol](https://bitol.io/) data
standards — **ODCS** (Open Data Contract Standard) and **ODPS** (Open Data
Product Standard).

Skills are authored to the canonical [agentskills.io specification](https://agentskills.io/specification),
so they're portable across Claude Code, the Claude Agent SDK, and any other
framework that consumes the format. Each skill is **self-contained** — once
installed, it does not fetch from the internet at runtime. The vendored
reference material under `skills/<name>/references/` is the mechanical truth;
the prose in `skills/<name>/SKILL.md` is the meaning layer.

## Skills

| Skill | What it covers | Spec versions |
|---|---|---|
| [`odcs-yaml`](skills/odcs-yaml/) | Open Data Contract Standard YAML format — structure, semantics, schema model, sections, version differences. | ODCS 3.0.0, 3.0.1, 3.0.2, 3.1.0 |
| [`odps-yaml`](skills/odps-yaml/) | Open Data Product Standard YAML format — data products, input/output/management ports, the contract-reference model. | ODPS 1.0.0 |
| [`odcs-python`](skills/odcs-python/) | The `open-data-contract-standard` PyPI package — `OpenDataContractStandard` Pydantic model, parsing, constructing, validating, the spec→pip version map. | ODCS 3.0.1, 3.0.2, 3.1.0 (via pip module) |

The three skills are independently installable. `odcs-yaml` and `odcs-python`
overlap somewhat — install both if you want full coverage of ODCS in YAML *and*
in Python, or install just one if you only need that side.

## Installing a skill

Skills install by copying the folder into your local skills directory. For
Claude Code, that's `~/.claude/skills/`:

```bash
# Clone or download this repo, then from the repo root:
cp -r skills/odcs-yaml    ~/.claude/skills/odcs-yaml
cp -r skills/odps-yaml    ~/.claude/skills/odps-yaml
cp -r skills/odcs-python  ~/.claude/skills/odcs-python
```

For other Agent SDK consumers, copy the same folder into whatever directory
that framework reads skills from. The folder is the unit — `SKILL.md` plus its
sibling `references/` subtree must move together.

To uninstall, delete the folder.

## What's in each skill folder

```
skills/<name>/
  SKILL.md         # frontmatter + body — loaded into agent context on activation
  sources.toml     # vendoring manifest (input to scripts/sync_specs.py)
  references/      # vendored upstream material — loaded on demand
```

`SKILL.md` is a few hundred lines of hand-written prose explaining how to
*think* about the spec; the body links to files under `references/` for the
mechanical details (full schemas, prose specs, examples, changelogs).

## Contributing

If you're modifying or adding a skill, the workflow is documented in:

- **[`CLAUDE.md`](CLAUDE.md)** — repository conventions, anti-patterns, and the
  drift workflow for keeping vendored material current.
- **[`SKILL_PLAYBOOK.md`](SKILL_PLAYBOOK.md)** — the step-by-step per-skill
  workflow for creating a new skill or updating an existing one.
- **[`REFERENCES.md`](REFERENCES.md)** — canonical upstream URLs (the source
  of truth for Bitol and Agent SDK links).

Quick commands once you have the repo cloned:

```bash
uv sync                                            # install Python deps
uv run scripts/validate_skill.py skills            # lint all skills
uv run scripts/sync_specs.py skills                # check vendored material vs upstream
uv run scripts/sync_specs.py skills --apply        # update vendored material
uv run pytest                                      # run the test suite
```

## License

The original work in this repo (skill prose, tooling, tests) is released under
the [MIT License](LICENSE).

The vendored material under each skill's `references/` directory is *not*
covered by that license — those files remain under their respective upstream
licenses. See the upstream repos linked in [`REFERENCES.md`](REFERENCES.md).
