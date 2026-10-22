# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`tex_tool` is a small Python library packaged as `tex_tool` with four CLI entry points for TeX, BibTeX, and LTeX workflows. It uses a `src/` layout and setuptools with `pyproject.toml`; the agent-skill tree ships as package data from `src/tex_tool/skills/` (`MANIFEST.in` + `include-package-data`).

## Commands

```bash
# Editable install
pip install -e .

# Run all tests (uses pytest, tmp_path fixture — no other plugins needed)
pytest

# Run a single test file
pytest tests/test_merge_bib.py

# Run a single test class
pytest tests/test_merge_bib.py::TestMergeBib

# CLI smoke
tex-tool --help
tex-tool bib add --help
```

## Architecture

**Package layout (`src/tex_tool/`):**

- `cli.py` — the single CLI entry point: builds the whole subcommand tree (`tex-tool bib ...`, `tex-tool dict ...`, `tex-tool clean`, `tex-tool abstract`) from the feature modules and dispatches. The only place that maps argv → run function.
- `bib/merge_bib.py` — merges multiple `.bib` files, removes duplicates by ID (and optionally by DOI). Core function: `remove_duplicates()` returns a 4-tuple of `(kept_dict, removed_list, same_entry_diff_doi_list, same_doi_groups_list)`; `parse_entries()` parses a BibTeX string into entries (nonstandard types such as `@software` accepted).
- `bib/entry_ops.py` — add / rename / search operations on `.bib` files (logic layer, no network). `add` appends the raw BibTeX text — existing formatting and comments are preserved — and fails hard on duplicate keys (nothing written); `rename` patches only the `@type{key,` header.
- `bib/scix.py` — request layer for the SciX/ADS export API: `export_bibtex(bibcode, token)` fetches one record. The only module that imports urllib; token comes from `--token` or env `SCIX_TOKEN`.
- `clean/comments.py` — wraps the external `arxiv_latex_cleaner` CLI (must be installed separately). Copies the input `.tex` to a temp directory, runs the cleaner, then optionally collapses 3+ consecutive blank lines to one. The subcommand takes a positional `input` argument (not `-i`).
- `abstract/extract.py` — extracts the `\begin{abstract}...\end{abstract}` block from a `.tex` file and converts it to arXiv-compatible plain text (macro expansion, font-command conversion, special-character replacement).
- `ltex/combine_dict.py` — merges two LTeX dictionary files by line-wise set union. Takes two positional arguments for the input files.
- `ltex/new_command_to_setting.py` — parses `\newcommand{...}{...}` lines from a `.tex` file and writes a JSON settings file mapping each command name to `"dummy"` (a placeholder that LTeX requires).
- `skills/` — the agent-skill tree shipped as package data (`SKILL-DEPLOY.md` plus one `<name>/skill/` + `meta.yaml` container per skill); `python -m tex_tool.skills` prints its directory and deployment guide.

**CLI tree** (single console script `tex-tool = "tex_tool.cli:main"` in `pyproject.toml`):

| Command | Module |
|---|---|
| `tex-tool bib merge` | `tex_tool.bib.merge_bib` |
| `tex-tool bib add` / `bib rename` / `bib search` | `tex_tool.bib.entry_ops` |
| `tex-tool clean` | `tex_tool.clean.comments` |
| `tex-tool dict merge` | `tex_tool.ltex.combine_dict` |
| `tex-tool dict new-command` | `tex_tool.ltex.new_command_to_setting` |
| `tex-tool abstract` | `tex_tool.abstract.extract` |

**Pattern conventions:**

- Every feature module follows the same structure: core logic functions → `COMMAND`/`COMMAND_HELP` constants → `add_subparser(subparsers)` (registers the subcommand, calls `parser.set_defaults(func=run)`) → `run(args)`. The only dispatch lives in `tex_tool.cli:main(argv)`; tests exercise the CLI via `main(["bib", "merge", ...])` without subprocess.
- Tests live in `tests/` with one file per module (`TestMergeBib`, `TestEntryOps`, `TestComments`, etc.). Tests use `tmp_path` for temp files and `capsys` for stdout/stderr capture — standard pytest fixtures, no custom conftest.
- Default values for CLI arguments are module-level constants (e.g., `DEFAULT_BIB_FOLDER`, `DEFAULT_REMOVE_SAME_DOI`, `SCIX_API_BASE`).
- Network boundary: only `bib/scix.py` talks to the network. Tests always mock `export_bibtex` — the suite never hits SciX; the one live test self-skips unless `SCIX_TOKEN` is set.
