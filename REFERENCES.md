# References

Upstream sources of truth for the skills in this repo. Fill in each `TODO` —
this file is the base all skills and tooling will pull from.

## Bitol — general

- **Bitol org homepage**: https://bitol.io/
- **Bitol GitHub org**: https://github.com/bitol-io

## ODCS — Open Data Contract Standard

- **Spec repo**: https://github.com/bitol-io/open-data-contract-standard
- **Spec docs / website**: Available in the github readme
- **Supported versions in this repo**: 3.0.0+ (see each skill's `metadata.spec_versions` for the exact versions in scope)
- **JSON Schema location(s)** (per version, if applicable): Available in the above repo
- **Example contracts (upstream)**: TODO

### ODCS — Python implementation

- **Package name on PyPI**: open-data-contract-standard
- **Repo**: https://github.com/datacontract/open-data-contract-standard-python
- **Docs**: The repo, sadly no real docs
- **Minimum / recommended version**: Only matching the versions mentioned above, a mapping is available in the python implementation repo

## ODPS — Open Data Product Standard

- **Spec repo**: Not yet available
- **Spec docs / website**: https://github.com/bitol-io/open-data-product-standard
- **Supported versions in this repo**: 1.0.0
- **JSON Schema location**: available in the above repo
- **Example products (upstream)**: TODO

## Agent SDK — skill format reference

We author skills in a format that is portable beyond Claude Code (Agent SDK
compatible).

- **Canonical Agent Skills specification**: https://agentskills.io/specification
- **Claude Agent SDK — Skills integration docs**: https://code.claude.com/docs/en/agent-sdk/skills
- **Anthropic's official skills repo (reference examples)**: https://github.com/anthropics/skills
- **Validator**: https://github.com/agentskills/agentskills/tree/main/skills-ref (`skills-ref validate ./my-skill`)
