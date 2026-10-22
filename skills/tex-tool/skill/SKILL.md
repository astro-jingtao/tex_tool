---
name: tex-tool
description: Use the tex-tool CLI for TeX, BibTeX, and LTeX chores — merge or dedupe .bib files, add BibTeX entries by SciX/ADS bibcode, rename or search entries, clean arXiv LaTeX, extract an arXiv-ready abstract, and manage LTeX dictionaries. Use when a task mentions .bib files, bibcodes, tex-tool commands, arxiv_latex_cleaner, LTeX dictionaries or settings, or preparing LaTeX for arXiv submission.
---

# tex-tool CLI

## Role

Drive the installed `tex-tool` CLI — the `tex_tool` Python package — for TeX, BibTeX, and LTeX chores. One entry point, `tex-tool <group> <command> ...`: the groups `bib` and `dict`, plus the top-level `clean` and `abstract`. Only `bib add --scix` touches the network.

Verify before first use in a session: `tex-tool --help` runs (the package is installed and importable). `tex-tool clean` additionally needs the external `arxiv_latex_cleaner` CLI on PATH.

To make this skill available to Claude Code on a machine, run `tex-tool skills-path` and follow the printed deployment guide.

# Command Reference

## bib — .bib file management

| Command | Effect |
| --- | --- |
| `tex-tool bib merge [-f FOLDER] [-o OUTPUT] [-r REPORT] [--remove-same-doi]` | Merge every `.bib` in FOLDER (default `files`) into OUTPUT (default `merged.bib`), dedupe by entry key, and write a report to REPORT (default `report.txt`). `--remove-same-doi` additionally drops entries that share a DOI. |
| `tex-tool bib add BIB_FILE (--scix BIBCODE \| --file SOURCE.bib) [--rename NEW_KEY] [--token TOKEN] [--api-base URL]` | Append entries to BIB_FILE as raw BibTeX text — existing formatting and comments are preserved; the file is created when missing. `--rename` requires exactly one incoming entry. |
| `tex-tool bib rename BIB_FILE OLD_KEY NEW_KEY` | Patch only the `@type{key,` header; every other byte of the file is untouched. |
| `tex-tool bib search QUERY [PATHS...] [--field NAME]` | Case-insensitive substring search; PATHS are `.bib` files or folders (default `./files`). Without `--field`, the entry key, entry type, and all field values are searched; `--field NAME` (title, author, doi, year, ...) restricts to that field, `--field key` to the entry key. Output is `[type] key: title` lines plus a count. |

`add` and `rename` raise before writing anything on a key collision — resolve the duplicate, never force:

- `add`: an incoming key already present in BIB_FILE, or duplicated inside the incoming batch → nothing is written.
- `rename`: OLD_KEY missing, OLD_KEY appearing more than once, NEW_KEY equal to OLD_KEY, or NEW_KEY already present → nothing is written.

## SciX fetch — `bib add --scix`

- Token: `--token` or the environment variable `SCIX_TOKEN` (generate one at https://scixplorer.org/user/settings/token). Never write the token into tracked files, logs, or reports.
- Default API base is `https://scixplorer.org`; when it is unreachable, `--api-base https://api.adsabs.harvard.edu` speaks the same wire API (an ADS token works there).

## clean / abstract — single .tex files

| Command | Effect |
| --- | --- |
| `tex-tool clean INPUT.tex [-o OUTPUT] [--keep-newlines]` | Run `arxiv_latex_cleaner` on a temp copy of INPUT; output defaults to `<stem>_cleaned.tex` beside the input. Blank-line runs of 3 or more collapse to one unless `--keep-newlines` is given. |
| `tex-tool abstract INPUT.tex [-o OUTPUT]` | Extract the `abstract` environment as arXiv-compatible plain text (preamble macro expansion, font-command conversion, special-character replacement). Default prints to stdout. |

## dict — LTeX support files

| Command | Effect |
| --- | --- |
| `tex-tool dict merge DICT1 DICT2 [-o OUTPUT]` | Line-wise set union of two LTeX dictionary files; OUTPUT defaults to `dict_combine.txt`. |
| `tex-tool dict new-command [-i INPUT] [-o OUTPUT]` | Parse `\newcommand{...}{...}` lines from INPUT (default `./new_command.tex`) into a JSON settings file mapping each command name to `"dummy"` (OUTPUT defaults to `./setting.json`). |

# Limits

- The skill drives the CLI. Module-level detail — parsing internals, the abstract pipeline's exact conversion rules — lives in the tex_tool repository's README; consult it before extending the package, not before using the CLI.
- No command edits entry field values: `rename` touches only keys, `add` only appends.

# Supporting Files

- `CHANGELOG.md` — this skill's change history; read when updating the skill.
