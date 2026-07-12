#!/usr/bin/env python3
"""Check upstream repos for releases newer than the refs pinned in sources.toml.

sources.toml pins immutable tags, so the drift check (sync_specs.py) can never
notice a *new* upstream release — this script closes that gap. For each skill,
it takes the highest semver tag pinned per upstream repo and compares it with
the newest semver tag upstream. Prerelease-style tags (v3.1.0-rc1,
v3.0.0-preview) are ignored on both sides.

Tags are listed with `git ls-remote --tags` rather than the GitHub REST API:
anonymous git reads on public repos need no token and have no API rate limit,
so the script behaves the same in CI and on a laptop.

Usage:
    uv run scripts/check_releases.py skills              # all skills
    uv run scripts/check_releases.py skills/odcs-yaml    # one skill

Exit codes:
    0  everything up to date
    1  newer upstream release(s) found
    2  invocation error, or tags could not be fetched
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SEMVER_TAG_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")

Version = tuple[int, int, int]


def parse_semver(tag: str) -> Version | None:
    m = SEMVER_TAG_RE.match(tag)
    return tuple(int(g) for g in m.groups()) if m else None


def fmt(version: Version) -> str:
    return "v" + ".".join(str(n) for n in version)


def fetch_tags(repo: str) -> list[str]:
    """List a repo's tag names via anonymous `git ls-remote --tags`."""
    proc = subprocess.run(
        ["git", "ls-remote", "--tags", f"https://github.com/{repo}.git"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-remote failed for {repo}: {proc.stderr.strip()}")
    tags = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].startswith("refs/tags/"):
            # annotated tags appear twice, once dereferenced as <name>^{}
            tags.append(parts[1].removeprefix("refs/tags/").removesuffix("^{}"))
    return tags


def find_skills(target: Path) -> list[Path]:
    """Return skill directories (each containing sources.toml)."""
    if (target / "sources.toml").exists():
        return [target]
    return sorted(p.parent for p in target.glob("*/sources.toml"))


def pinned_by_repo(skill_dir: Path) -> dict[str, Version]:
    """Highest semver ref pinned per upstream repo in a skill's sources.toml."""
    with (skill_dir / "sources.toml").open("rb") as f:
        data = tomllib.load(f)
    pinned: dict[str, Version] = {}
    for src in data.get("source", []):
        repo = src.get("repo")
        ref = src.get("ref")
        if not repo or not ref:
            continue
        version = parse_semver(ref)
        if version is None:
            print(
                f"  WARN   [{skill_dir.name}] ref {ref!r} for {repo} "
                "is not a semver tag; skipping",
                file=sys.stderr,
            )
            continue
        if repo not in pinned or version > pinned[repo]:
            pinned[repo] = version
    return pinned


def check(skills: list[Path], fetch=fetch_tags) -> tuple[list[str], int]:
    """Compare pinned refs against upstream tags. Returns (report_lines, exit_code)."""
    lines: list[str] = []
    outdated = 0
    errors = 0
    tag_cache: dict[str, list[str] | None] = {}

    for skill in skills:
        for repo, pinned in sorted(pinned_by_repo(skill).items()):
            if repo not in tag_cache:
                try:
                    tag_cache[repo] = fetch(repo)
                except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
                    print(f"  ERROR  fetching tags for {repo}: {e}", file=sys.stderr)
                    tag_cache[repo] = None
            tags = tag_cache[repo]
            if tags is None:
                lines.append(f"ERROR   [{skill.name}] {repo}: could not fetch tags")
                errors += 1
                continue
            upstream_versions = [v for t in tags if (v := parse_semver(t)) is not None]
            if not upstream_versions:
                lines.append(f"ERROR   [{skill.name}] {repo}: no semver tags found upstream")
                errors += 1
                continue
            newest = max(upstream_versions)
            if newest > pinned:
                lines.append(
                    f"UPDATE  [{skill.name}] {repo}: "
                    f"pinned {fmt(pinned)}, newest upstream {fmt(newest)}"
                )
                outdated += 1
            else:
                lines.append(f"ok      [{skill.name}] {repo}: {fmt(pinned)} is the newest release")

    if outdated:
        return (lines, 1)
    if errors:
        return (lines, 2)
    return (lines, 0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="A skill dir or skills/")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"error: {args.path} does not exist", file=sys.stderr)
        return 2

    skills = find_skills(args.path)
    if not skills:
        print(f"error: no skills (sources.toml) found under {args.path}", file=sys.stderr)
        return 2

    lines, code = check(skills)
    for line in lines:
        print(line)
    updates = sum(1 for line in lines if line.startswith("UPDATE"))
    print(f"\nsummary: {updates} upstream release(s) newer than pinned refs")
    if updates:
        print("(update sources.toml refs, run sync_specs.py --apply, then update SKILL.md)")
    return code


if __name__ == "__main__":
    sys.exit(main())
