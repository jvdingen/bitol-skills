"""Per-skill example-parsing tests.

For every vendored example file under skills/<name>/references/examples/,
assert that:
  - it loads as YAML
  - it is a mapping at the root
  - it declares the apiVersion / kind fields the spec requires

These tests catch drift between the upstream examples and the spec families
the skills target. They do not check semantics — that's the schema validator's
job — but they catch a broken vendoring run, an empty file, a YAML syntax
error, or an upstream switch to a different document shape.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
EXAMPLE_FILES = sorted(REPO_ROOT.glob("skills/*/references/examples/*.yaml"))


def _example_id(path: Path) -> str:
    # path is .../skills/<skill>/references/examples/<file>.yaml
    return f"{path.parent.parent.parent.name}/{path.name}"


@pytest.mark.parametrize("example", EXAMPLE_FILES, ids=_example_id)
def test_example_parses_as_yaml_mapping(example: Path) -> None:
    with example.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{example.name} is not a YAML mapping at the root"
    assert "apiVersion" in data, f"{example.name} is missing apiVersion"
    assert "kind" in data, f"{example.name} is missing kind"


def test_at_least_one_example_per_skill_with_examples_dir() -> None:
    """If a skill has a references/examples/ dir, it should not be empty."""
    skills_with_examples_dir = sorted(
        d.parent.parent for d in REPO_ROOT.glob("skills/*/references/examples")
    )
    for skill in skills_with_examples_dir:
        examples = list(skill.glob("references/examples/*.yaml"))
        assert examples, f"{skill.name} has an empty examples/ directory"


def test_example_files_are_discovered() -> None:
    """Sanity check: the parametrize collected something.

    If this fails, the glob is wrong or the vendoring step has not run.
    Without this check, parametrize over an empty list silently passes.
    """
    assert EXAMPLE_FILES, "no example files found under skills/*/references/examples/"
