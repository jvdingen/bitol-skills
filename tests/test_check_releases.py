"""Tests for scripts/check_releases.py.

The tag-fetching side is injected, so these run offline. Live behavior is
covered by the daily upstream-checks workflow.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_releases import check, parse_semver, pinned_by_repo  # noqa: E402


def make_skill(tmp_path: Path, name: str, sources: str) -> Path:
    skill = tmp_path / name
    skill.mkdir()
    (skill / "sources.toml").write_text(sources)
    return skill


SOURCES = """\
[[source]]
repo = "example/spec"
ref  = "v1.0.0"
src  = "schema.json"
dest = "references/schema.json"

[[source]]
repo = "example/spec"
ref  = "v1.1.0"
src  = "docs.md"
dest = "references/docs.md"
"""


def test_parse_semver():
    assert parse_semver("v3.1.0") == (3, 1, 0)
    assert parse_semver("3.1.0") == (3, 1, 0)
    assert parse_semver("v3.0.0-preview") is None
    assert parse_semver("v3.1.0-rc1") is None
    assert parse_semver("main") is None


def test_pinned_by_repo_takes_highest_ref(tmp_path):
    skill = make_skill(tmp_path, "test-skill", SOURCES)
    assert pinned_by_repo(skill) == {"example/spec": (1, 1, 0)}


def test_up_to_date_exits_zero(tmp_path):
    skill = make_skill(tmp_path, "test-skill", SOURCES)
    lines, code = check([skill], fetch=lambda repo: ["v1.0.0", "v1.1.0"])
    assert code == 0
    assert any(line.startswith("ok") for line in lines)


def test_newer_release_detected(tmp_path):
    skill = make_skill(tmp_path, "test-skill", SOURCES)
    lines, code = check([skill], fetch=lambda repo: ["v1.0.0", "v1.1.0", "v1.2.0"])
    assert code == 1
    assert any("pinned v1.1.0, newest upstream v1.2.0" in line for line in lines)


def test_prerelease_tags_ignored(tmp_path):
    skill = make_skill(tmp_path, "test-skill", SOURCES)
    lines, code = check([skill], fetch=lambda repo: ["v1.1.0", "v2.0.0-rc1", "v2.0.0-preview"])
    assert code == 0


def test_fetch_failure_exits_two(tmp_path):
    skill = make_skill(tmp_path, "test-skill", SOURCES)

    def boom(repo):
        raise RuntimeError("network down")

    lines, code = check([skill], fetch=boom)
    assert code == 2
    assert any("could not fetch tags" in line for line in lines)


def test_repo_fetched_once_across_skills(tmp_path):
    calls: list[str] = []

    def fetch(repo):
        calls.append(repo)
        return ["v1.1.0"]

    a = make_skill(tmp_path, "skill-a", SOURCES)
    b = make_skill(tmp_path, "skill-b", SOURCES)
    _, code = check([a, b], fetch=fetch)
    assert code == 0
    assert calls == ["example/spec"]


def test_real_sources_have_semver_refs():
    """Every ref pinned by the real skills must be a semver tag, otherwise the
    release check silently skips it."""
    for manifest in sorted(REPO_ROOT.glob("skills/*/sources.toml")):
        pinned = pinned_by_repo(manifest.parent)
        assert pinned, f"{manifest} pins no semver-tagged sources"
