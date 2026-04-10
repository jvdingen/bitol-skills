#!/usr/bin/env python3
"""Validate skills against the agentskills.io spec + project conventions.

Spec rules (from https://agentskills.io/specification):
    - SKILL.md exists with parseable YAML frontmatter
    - frontmatter has only allowed fields
    - name: 1-64 chars, [a-z0-9-], no leading/trailing/consecutive hyphens
    - name matches parent directory
    - description: 1-1024 chars

Project rules:
    - metadata.spec_versions present, list of semver strings (X.Y.Z)
    - if sources.toml exists, references/ must exist
    - directory is references/ (plural), never reference/
    - SKILL.md body should be < 500 lines (warning, not error)

Usage:
    uv run scripts/validate_skill.py skills/odcs-yaml    # one skill
    uv run scripts/validate_skill.py skills              # all skills

Exit codes:
    0  all skills validated cleanly
    1  one or more skills failed validation
    2  invocation error
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_CHARSET_RE = re.compile(r"^[a-z0-9-]+$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
WARN_BODY_LINES = 500


def parse_frontmatter(skill_md: Path) -> tuple[dict | None, str, list[str]]:
    """Returns (frontmatter, body, errors). frontmatter is None on error."""
    if not skill_md.exists():
        return (None, "", [f"missing SKILL.md at {skill_md}"])
    text = skill_md.read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not m:
        return (None, "", ["SKILL.md missing or malformed YAML frontmatter (--- ... ---)"])
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return (None, "", [f"frontmatter YAML parse error: {e}"])
    if not isinstance(fm, dict):
        return (None, "", ["frontmatter is not a YAML mapping"])
    return (fm, m.group(2), [])


def validate_name(fm: dict, expected: str) -> list[str]:
    errors: list[str] = []
    name = fm.get("name")
    if name is None:
        return ["frontmatter missing required field: name"]
    if not isinstance(name, str):
        return [f"name must be a string, got {type(name).__name__}"]
    if len(name) < 1 or len(name) > MAX_NAME:
        errors.append(f"name length {len(name)} not in [1, {MAX_NAME}]")
    if not NAME_CHARSET_RE.match(name):
        errors.append(f"name {name!r} contains invalid chars (allowed: a-z 0-9 -)")
    if name.startswith("-") or name.endswith("-"):
        errors.append(f"name {name!r} cannot start or end with -")
    if "--" in name:
        errors.append(f"name {name!r} cannot contain consecutive hyphens")
    if name != expected:
        errors.append(f"name {name!r} does not match parent directory {expected!r}")
    return errors


def validate_description(fm: dict) -> list[str]:
    desc = fm.get("description")
    if desc is None:
        return ["frontmatter missing required field: description"]
    if not isinstance(desc, str):
        return [f"description must be a string, got {type(desc).__name__}"]
    if len(desc) < 1 or len(desc) > MAX_DESCRIPTION:
        return [f"description length {len(desc)} not in [1, {MAX_DESCRIPTION}]"]
    return []


def validate_compatibility(fm: dict) -> list[str]:
    compat = fm.get("compatibility")
    if compat is None:
        return []
    if not isinstance(compat, str):
        return [f"compatibility must be a string, got {type(compat).__name__}"]
    if len(compat) > MAX_COMPATIBILITY:
        return [f"compatibility length {len(compat)} > {MAX_COMPATIBILITY}"]
    return []


def validate_allowed_fields(fm: dict) -> list[str]:
    extra = set(fm.keys()) - ALLOWED_FRONTMATTER_FIELDS
    if extra:
        return [f"unknown frontmatter fields: {sorted(extra)}"]
    return []


def validate_spec_versions(fm: dict) -> list[str]:
    """Project rule: metadata.spec_versions must be a non-empty list of semver strings."""
    metadata = fm.get("metadata")
    if metadata is None:
        return ["project rule: metadata.spec_versions is required"]
    if not isinstance(metadata, dict):
        return ["metadata must be a mapping if present"]
    sv = metadata.get("spec_versions")
    if sv is None:
        return ["project rule: metadata.spec_versions is required"]
    if not isinstance(sv, list) or not sv:
        return ["metadata.spec_versions must be a non-empty list"]
    errors = []
    for v in sv:
        if not isinstance(v, str) or not SEMVER_RE.match(v):
            errors.append(f"metadata.spec_versions entry {v!r} not a semver string (X.Y.Z)")
    return errors


def validate_layout(skill_dir: Path) -> list[str]:
    """Project rule: references/ exists if sources.toml exists; never reference/ singular."""
    errors = []
    if (skill_dir / "sources.toml").exists() and not (skill_dir / "references").is_dir():
        errors.append("project rule: sources.toml exists but references/ is missing (run sync_specs.py --apply)")
    if (skill_dir / "reference").exists():
        errors.append("project rule: directory must be 'references/' (plural), not 'reference/'")
    return errors


def validate_body_length(body: str) -> list[str]:
    n = body.count("\n")
    if n > WARN_BODY_LINES:
        return [f"WARN: SKILL.md body is {n} lines (recommended < {WARN_BODY_LINES}); push detail into references/"]
    return []


def validate_skill(skill_dir: Path) -> list[str]:
    fm, body, parse_errors = parse_frontmatter(skill_dir / "SKILL.md")
    if parse_errors:
        return parse_errors
    assert fm is not None
    errors: list[str] = []
    errors += validate_allowed_fields(fm)
    errors += validate_name(fm, skill_dir.name)
    errors += validate_description(fm)
    errors += validate_compatibility(fm)
    errors += validate_spec_versions(fm)
    errors += validate_layout(skill_dir)
    errors += validate_body_length(body)
    return errors


def discover_skills(path: Path) -> list[Path]:
    if (path / "SKILL.md").exists():
        return [path]
    return sorted(p.parent for p in path.glob("*/SKILL.md"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    if not args.path.exists():
        print(f"error: {args.path} does not exist", file=sys.stderr)
        return 2

    skills = discover_skills(args.path)
    if not skills:
        print(f"error: no skills (SKILL.md) found under {args.path}", file=sys.stderr)
        return 2

    failed = 0
    for skill in skills:
        errors = validate_skill(skill)
        warnings = [e for e in errors if e.startswith("WARN")]
        hard = [e for e in errors if not e.startswith("WARN")]
        status = "OK" if not hard else "FAIL"
        print(f"[{status}] {skill}")
        for w in warnings:
            print(f"  {w}")
        for h in hard:
            print(f"  {h}")
        if hard:
            failed += 1

    print(f"\nsummary: {len(skills) - failed}/{len(skills)} skills passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
