# Changelog — tex-tool

Notable changes, newest first.

## 2026-10-22

### Changed
- Single discovery entry `python -m tex_tool.skills`: the skill body, deployment guide, and package metadata all name it as the one way to locate the skills directory.

### Removed
- `tex-tool skills-path` subcommand — the second of two discovery entries for the same directory; the module entry needs no console script.

## 2026-10-22

### Changed
- Skills root moved inside the package: the tree lives at `src/tex_tool/skills/` (installed: `tex_tool/skills/`) instead of the repository root — a checkout-only directory never reaches the consumer.
- `setup.py` build hook removed; the tree ships as package data via MANIFEST.in + include-package-data.
### Added
- Discovery entry `python -m tex_tool.skills`: prints the skills directory and its deployment-guide path.

## 2026-10-22

### Changed
- Skill tree lives at the repository root (`skills/` beside `src/`) and ships inside the package (`tex_tool/skills/`) at build time; the deployment guide deploys from the installed location.
### Added
- `tex-tool skills-path` command printing the packaged skills directory — the deployment entry point named by the guide and the skill body.

## 2026-10-22

### Added
- Initial skill at the package's skills root (`skills/tex-tool/`): full tex-tool command reference — bib merge/add/rename/search, clean, abstract, dict merge/new-command — with defaults, failure semantics, and SciX token discipline.
- `meta.yaml` declaring the `tex-tool` and `arxiv_latex_cleaner` CLI requirements.
- Deployment guide `skills/SKILL-DEPLOY.md`.

### Removed
- Previous copy kept tracked at the repository's `.claude/skills/tex-tool/` — a deployment location, not a source location.
