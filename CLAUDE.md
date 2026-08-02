# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`tex_tool` is a small Python library packaged as `tex_tool` with four CLI entry points for TeX, BibTeX, and LTeX workflows. It uses a `src/` layout and setuptools with `pyproject.toml`.

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
```

## Architecture

**Package layout (`src/tex_tool/`):**

- `bib/merge_bib.py` — merges multiple `.bib` files, removes duplicates by ID (and optionally by DOI). Core function: `remove_duplicates()` returns a 4-tuple of `(kept_dict, removed_list, same_entry_diff_doi_list, same_doi_groups_list)`. All `main()` functions accept an optional `argv: list[str] | None` parameter so they can be tested without subprocess.
- `clean/comments.py` — wraps the external `arxiv_latex_cleaner` CLI (must be installed separately). Copies the input `.tex` to a temp directory, runs the cleaner, then optionally collapses 3+ consecutive blank lines to one. The entry point takes a positional `input` argument (not `-i`).
- `ltex/combine_dict.py` — merges two LTeX dictionary files by line-wise set union. Entry point takes two positional arguments for the input files.
- `ltex/new_command_to_setting.py` — parses `\newcommand{...}{...}` lines from a `.tex` file and writes a JSON settings file mapping each command name to `"dummy"` (a placeholder that LTeX requires).

**CLI entry points** (defined in `pyproject.toml` `[project.scripts]`):

| Command | Module |
|---|---|
| `tex-tool-merge-bib` | `tex_tool.bib.merge_bib:main` |
| `tex-tool-clean-comments` | `tex_tool.clean.comments:main` |
| `tex-tool-combine-dict` | `tex_tool.ltex.combine_dict:main` |
| `tex-tool-new-command` | `tex_tool.ltex.new_command_to_setting:main` |

**Pattern conventions:**

- Every module follows the same structure: core logic function(s) → `build_parser()` → `main(argv=None)`. The `main` function is testable by passing a list of CLI args.
- Tests live in `tests/` with one file per module. Each test file contains a single class (`TestMergeBib`, `TestComments`, etc.). Tests use `tmp_path` for temp files and `capsys` for stdout/stderr capture — standard pytest fixtures, no custom conftest.
- Default values for CLI arguments are module-level constants (e.g., `DEFAULT_BIB_FOLDER`, `DEFAULT_REMOVE_SAME_DOI`).
