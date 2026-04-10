"""Tests for scripts/validate_skill.py."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_skill import validate_skill  # noqa: E402


def make_skill(
    tmp_path: Path,
    name: str,
    frontmatter: str,
    body: str = "# Body\n",
    make_refs: bool = False,
    make_sources: bool = False,
) -> Path:
    skill = tmp_path / name
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}")
    if make_refs:
        (skill / "references").mkdir()
    if make_sources:
        (skill / "sources.toml").write_text("")
    return skill


VALID_FM = """\
name: test-skill
description: A test skill for validation.
metadata:
  spec_versions:
    - "1.0.0"
"""


def test_real_odcs_yaml_validates_clean():
    """The actual odcs-yaml skill must validate cleanly (no hard errors)."""
    skill = REPO_ROOT / "skills" / "odcs-yaml"
    errors = [e for e in validate_skill(skill) if not e.startswith("WARN")]
    assert errors == [], f"odcs-yaml should validate cleanly; got: {errors}"


def test_minimal_valid_skill_passes(tmp_path):
    skill = make_skill(tmp_path, "test-skill", VALID_FM.strip())
    errors = [e for e in validate_skill(skill) if not e.startswith("WARN")]
    assert errors == []


def test_missing_skill_md(tmp_path):
    skill = tmp_path / "test-skill"
    skill.mkdir()
    errors = validate_skill(skill)
    assert any("missing SKILL.md" in e for e in errors)


def test_missing_frontmatter(tmp_path):
    skill = tmp_path / "test-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# No frontmatter here\n")
    errors = validate_skill(skill)
    assert any("frontmatter" in e for e in errors)


def test_missing_description_fails(tmp_path):
    fm = "name: test-skill\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("description" in e for e in errors)


def test_missing_name_fails(tmp_path):
    fm = "description: foo\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("missing required field: name" in e for e in errors)


def test_name_mismatch_fails(tmp_path):
    fm = "name: wrong-name\ndescription: foo\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "real-name", fm.strip())
    errors = validate_skill(skill)
    assert any("does not match parent directory" in e for e in errors)


def test_consecutive_hyphens_fail(tmp_path):
    fm = "name: bad--name\ndescription: foo\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "bad--name", fm.strip())
    errors = validate_skill(skill)
    assert any("consecutive hyphens" in e for e in errors)


def test_uppercase_name_fails(tmp_path):
    fm = "name: BadName\ndescription: foo\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "BadName", fm.strip())
    errors = validate_skill(skill)
    assert any("invalid chars" in e for e in errors)


def test_description_too_long_fails(tmp_path):
    fm = f"name: test-skill\ndescription: '{'x' * 1025}'\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("description length" in e for e in errors)


def test_unknown_field_fails(tmp_path):
    fm = "name: test-skill\ndescription: foo\nfoo: bar\nmetadata:\n  spec_versions:\n    - '1.0.0'\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("unknown frontmatter fields" in e for e in errors)


def test_missing_spec_versions_fails(tmp_path):
    fm = "name: test-skill\ndescription: foo\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("spec_versions" in e for e in errors)


def test_bad_spec_version_format_fails(tmp_path):
    fm = "name: test-skill\ndescription: foo\nmetadata:\n  spec_versions:\n    - 'not-a-version'\n"
    skill = make_skill(tmp_path, "test-skill", fm.strip())
    errors = validate_skill(skill)
    assert any("semver" in e for e in errors)


def test_sources_toml_without_references_fails(tmp_path):
    skill = make_skill(tmp_path, "test-skill", VALID_FM.strip(), make_sources=True)
    errors = validate_skill(skill)
    assert any("references/ is missing" in e for e in errors)


def test_singular_reference_dir_fails(tmp_path):
    skill = make_skill(tmp_path, "test-skill", VALID_FM.strip())
    (skill / "reference").mkdir()
    errors = validate_skill(skill)
    assert any("plural" in e for e in errors)


def test_long_body_warns(tmp_path):
    body = "\n".join(f"line {i}" for i in range(600)) + "\n"
    skill = make_skill(tmp_path, "test-skill", VALID_FM.strip(), body=body)
    errors = validate_skill(skill)
    warnings = [e for e in errors if e.startswith("WARN")]
    assert any("body is" in w for w in warnings)
