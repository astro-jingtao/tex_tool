---
name: tex-tool
description: Use the tex_tool CLI for TeX/BibTeX/LTeX chores in this repository — merge or dedupe .bib files, add entries by SciX bibcode, rename or search entries, clean arXiv TeX, and manage LTeX dictionaries. Use when a task mentions .bib file management, tex-tool commands, bibcodes, or arxiv_latex_cleaner.
---

# tex-tool CLI

Single entry point: `tex-tool <group> ...`. Everything runs offline except `tex-tool bib add --scix`.

## BibTeX — `tex-tool bib ...`

- Merge/dedupe a folder of .bib files: `tex-tool bib merge -f files -o merged.bib -r report.txt [--remove-same-doi]`
- Add an entry by SciX/ADS bibcode: `tex-tool bib add refs.bib --scix 2024ApJS..272...24C [--rename jing2024]`
  - Token: `--token` or env `SCIX_TOKEN` (generate at https://scixplorer.org/user/settings/token).
  - If the SciX base is unreachable/wrong: `--api-base https://api.adsabs.harvard.edu` (same wire API, ADS token).
  - Add from a local file instead: `--file source.bib` (mutually exclusive with `--scix`).
- Rename an entry key: `tex-tool bib rename refs.bib old_key new_key`
- Search: `tex-tool bib search "dark matter" [paths...] [--field title]` — default paths `./files`; omit `--field` to search keys + all fields (case-insensitive substring).
- add/rename FAIL on duplicate entry keys (nothing is written on failure) — resolve the duplicate, never force.
- add appends raw text; rename patches only the `@type{key,` header — existing formatting/comments are preserved.

## TeX / LTeX — `tex-tool clean|abstract|dict ...`

- `tex-tool clean main.tex [-o out.tex] [--keep-newlines]` — needs the external `arxiv_latex_cleaner` CLI installed.
- `tex-tool abstract main.tex [-o abstract.txt]` — arXiv-compatible abstract extraction.
- `tex-tool dict merge a.txt b.txt -o out.txt` and `tex-tool dict new-command -i nc.tex -o setting.json`.

## Tests

`pytest`. Class-based; CLI behavior is tested via `tex_tool.cli.main([...])`. Network calls are always mocked in tests — never hit SciX from the suite; the one live test is skipped unless `SCIX_TOKEN` is set.
