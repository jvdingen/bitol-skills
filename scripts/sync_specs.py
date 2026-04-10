#!/usr/bin/env python3
"""Sync vendored upstream material for skills.

Reads each skill's sources.toml and fetches the declared upstream files into
the skill's references/ tree. Default mode is plan (no writes); pass --apply
to actually write files.

Examples:
    uv run scripts/sync_specs.py skills              # plan all skills
    uv run scripts/sync_specs.py skills/odcs-yaml    # plan one skill
    uv run scripts/sync_specs.py skills --apply      # write all skills

Sources are fetched from raw.githubusercontent.com (no auth required for
public repos). Refs in sources.toml MUST be tags, not branches — vendoring
from a moving branch breaks reproducibility.

Exit codes:
    0  no drift (or --apply succeeded)
    1  drift detected in plan mode, or fetch errors
    2  invocation error
"""

import argparse
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{src}"


def fetch(repo: str, ref: str, src: str) -> bytes:
    url = GITHUB_RAW.format(repo=repo, ref=ref, src=src)
    req = urllib.request.Request(url, headers={"User-Agent": "bitol-skills-sync/1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def find_skills(target: Path) -> list[Path]:
    """Return skill directories (each containing sources.toml)."""
    if (target / "sources.toml").exists():
        return [target]
    return sorted(p.parent for p in target.glob("*/sources.toml"))


def sync_skill(skill_dir: Path, apply: bool) -> tuple[int, int, int]:
    """Sync one skill. Returns (drift_count, error_count, total_count)."""
    manifest = skill_dir / "sources.toml"
    with manifest.open("rb") as f:
        data = tomllib.load(f)
    sources = data.get("source", [])
    if not sources:
        print("  (no [[source]] entries)")
        return (0, 0, 0)

    drift = 0
    errors = 0
    for src in sources:
        try:
            repo = src["repo"]
            ref = src["ref"]
            src_path = src["src"]
            dest = skill_dir / src["dest"]
        except KeyError as e:
            print(f"  ERROR  malformed [[source]] entry: missing {e}")
            errors += 1
            continue

        rel = dest.relative_to(skill_dir)
        try:
            upstream = fetch(repo, ref, src_path)
        except urllib.error.HTTPError as e:
            print(f"  ERROR  {rel}  HTTP {e.code} from {repo}@{ref}/{src_path}")
            errors += 1
            continue
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  ERROR  {rel}  network: {e}")
            errors += 1
            continue

        local = dest.read_bytes() if dest.exists() else None
        if local == upstream:
            print(f"  ok     {rel}")
        elif local is None:
            print(f"  new    {rel}")
            drift += 1
            if apply:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(upstream)
        else:
            print(f"  drift  {rel}  ({len(local)}B → {len(upstream)}B)")
            drift += 1
            if apply:
                dest.write_bytes(upstream)

    return (drift, errors, len(sources))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="A skill dir or skills/")
    parser.add_argument(
        "--apply", action="store_true", help="Write changes (default: plan only)"
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"error: {args.path} does not exist", file=sys.stderr)
        return 2

    skills = find_skills(args.path)
    if not skills:
        print(f"error: no skills (sources.toml) found under {args.path}", file=sys.stderr)
        return 2

    total_drift = 0
    total_errors = 0
    total_files = 0
    for skill in skills:
        print(f"\n[{skill.name}]")
        d, e, n = sync_skill(skill, args.apply)
        total_drift += d
        total_errors += e
        total_files += n

    verb = "applied" if args.apply else "would change"
    print(
        f"\nsummary: {total_drift}/{total_files} files {verb}, {total_errors} errors"
    )
    if total_errors:
        return 1
    if not args.apply and total_drift > 0:
        print("(re-run with --apply to write)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
