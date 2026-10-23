"""Add, rename, and search operations on .bib files.

Logic only — the single network interaction (fetching a BibTeX record from
SciX) lives in :mod:`tex_tool.bib.scix` and is called by ``run_add``.
"""

import argparse
from collections import Counter
import os
from pathlib import Path
import re
from typing import Optional

from tex_tool.bib.merge_bib import (
    DEFAULT_BIB_FOLDER,
    parse_entries,
    read_all_bibs,
    read_entries,
)
from tex_tool.bib.scix import ADS_API_BASE, SCIX_API_BASE, export_bibtex

SCIX_TOKEN_ENV = "SCIX_TOKEN"


def _rename_key_in_text(text: str, old_key: str, new_key: str) -> str:
    """Replace the first ``@type{old_key,`` header with the new key."""
    pattern = re.compile(r"(@\w+\s*\{\s*)" + re.escape(old_key) + r"(\s*,)")
    new_text, count = pattern.subn(rf"\g<1>{new_key}\g<2>", text, count=1)
    if count == 0:
        raise ValueError(f"entry key '{old_key}' not found in BibTeX text")
    return new_text


def add_entries(bib_file: str, bibtex_text: str, rename: Optional[str] = None) -> list[str]:
    """Append the entries in *bibtex_text* to *bib_file*.

    The target file is created when missing; existing content and formatting
    are untouched (the text is appended, never re-serialized). Raises
    ValueError when an incoming key is already in the file or is duplicated
    inside the batch — nothing is written in that case.
    """
    incoming = parse_entries(bibtex_text)
    if not incoming:
        raise ValueError("no BibTeX entries found in the given source")
    if rename is not None:
        if len(incoming) != 1:
            raise ValueError(f"--rename needs exactly one incoming entry, found {len(incoming)}")
        bibtex_text = _rename_key_in_text(bibtex_text, incoming[0]["ID"], rename)
        incoming[0]["ID"] = rename

    existing_ids = (
        {entry["ID"] for entry in read_entries(bib_file)} if Path(bib_file).exists() else set()
    )
    problems = []
    duplicate_in_file = [e["ID"] for e in incoming if e["ID"] in existing_ids]
    if duplicate_in_file:
        problems.append(f"key(s) already in {bib_file}: {', '.join(duplicate_in_file)}")
    duplicate_in_batch = sorted(
        key for key, n in Counter(e["ID"] for e in incoming).items() if n > 1
    )
    if duplicate_in_batch:
        problems.append(f"duplicate key(s) in the incoming batch: {', '.join(duplicate_in_batch)}")
    if problems:
        raise ValueError("; ".join(problems))

    with open(bib_file, "a", encoding="utf-8") as bib:
        bib.write(bibtex_text.strip() + "\n\n")
    return [entry["ID"] for entry in incoming]


def rename_entry(bib_file: str, old_key: str, new_key: str) -> None:
    """Rename entry *old_key* to *new_key* in *bib_file*, preserving formatting."""
    entries = read_entries(bib_file)
    ids = [entry["ID"] for entry in entries]
    if old_key not in ids:
        raise ValueError(f"entry key '{old_key}' not found in {bib_file}")
    if ids.count(old_key) > 1:
        raise ValueError(
            f"entry key '{old_key}' appears {ids.count(old_key)} times in "
            f"{bib_file}; fix the file first"
        )
    if new_key == old_key:
        raise ValueError("new key equals the old key")
    if new_key in ids:
        raise ValueError(f"entry key '{new_key}' already exists in {bib_file}")

    text = Path(bib_file).read_text(encoding="utf-8")
    Path(bib_file).write_text(_rename_key_in_text(text, old_key, new_key), encoding="utf-8")


def collect_entries(paths: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in paths:
        if os.path.isdir(path):
            entries += read_all_bibs(path)
        else:
            entries += read_entries(path)
    return entries


def search_entries(
    paths: list[str], query: str, field: Optional[str] = None
) -> list[dict[str, str]]:
    """Case-insensitive substring search over .bib entries.

    With *field* (e.g. ``title``, ``author``, ``doi``, ``year``; ``key``
    matches the entry key) only that field is searched; without it, every
    field value, the key, and the entry type are searched.
    """
    matches: list[dict[str, str]] = []
    for entry in collect_entries(paths):
        if field is None:
            haystack = " ".join(str(value) for value in entry.values())
        else:
            name = "ID" if field.lower() in ("key", "id") else field.lower()
            if name not in entry:
                continue
            haystack = str(entry[name])
        if query.lower() in haystack.lower():
            matches.append(entry)
    return matches


def run_add(args: argparse.Namespace) -> None:
    if args.scix:
        token = args.token or os.environ.get(SCIX_TOKEN_ENV)
        if not token:
            raise ValueError(f"SciX API token missing: pass --token or set ${SCIX_TOKEN_ENV}")
        bibtex_text = export_bibtex(args.scix, token, base_url=args.api_base)
    else:
        bibtex_text = Path(args.file).read_text(encoding="utf-8")
    added = add_entries(args.bib_file, bibtex_text, rename=args.rename)
    plural = "y" if len(added) == 1 else "ies"
    print(f"Added {len(added)} entr{plural} to {args.bib_file}: {', '.join(added)}")


def run_rename(args: argparse.Namespace) -> None:
    rename_entry(args.bib_file, args.old_key, args.new_key)
    print(f"Renamed '{args.old_key}' to '{args.new_key}' in {args.bib_file}")


def run_search(args: argparse.Namespace) -> None:
    matches = search_entries(args.files, args.query, field=args.field)
    if not matches:
        print("No entries found.")
        return
    for entry in matches:
        print(f"[{entry.get('ENTRYTYPE', '?')}] {entry.get('ID', '?')}: {entry.get('title', '')}")
    plural = "y" if len(matches) == 1 else "ies"
    print(f"\n{len(matches)} entr{plural} found.")


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    add = subparsers.add_parser(
        "add", help="Add a BibTeX entry from SciX (by bibcode) or from a .bib file"
    )
    source = add.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--scix",
        metavar="BIBCODE",
        help="fetch the entry with this SciX/ADS bibcode",
    )
    source.add_argument("--file", help="take the entry(ies) from this .bib file")
    add.add_argument("bib_file", help="target .bib file (created if missing)")
    add.add_argument(
        "--rename",
        metavar="NEW_KEY",
        help="rename the incoming entry key before adding",
    )
    add.add_argument("--token", help=f"SciX API token (default: env ${SCIX_TOKEN_ENV})")
    add.add_argument(
        "--api-base",
        default=SCIX_API_BASE,
        metavar="URL",
        help=f"export API base URL (default: {SCIX_API_BASE}; ADS: {ADS_API_BASE})",
    )
    add.set_defaults(func=run_add)

    rename = subparsers.add_parser("rename", help="Rename an entry key in a .bib file")
    rename.add_argument("bib_file", help=".bib file to edit")
    rename.add_argument("old_key", help="current entry key")
    rename.add_argument("new_key", help="new entry key")
    rename.set_defaults(func=run_rename)

    search = subparsers.add_parser("search", help="Search entries in .bib files or folders")
    search.add_argument("query", help="case-insensitive substring to find")
    search.add_argument(
        "files",
        nargs="*",
        default=[DEFAULT_BIB_FOLDER],
        help=".bib files or folders to search (default: ./files)",
    )
    search.add_argument(
        "--field",
        metavar="NAME",
        help="search only this field (title, author, doi, year, ...; 'key' = entry key)",
    )
    search.set_defaults(func=run_search)
