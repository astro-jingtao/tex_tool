"""Single-entry CLI: composes the subcommand tree from the feature modules.

Every feature module exposes ``add_subparser(subparsers)`` (registers its
command(s) and calls ``parser.set_defaults(func=run)``) plus ``run(args)``;
this module only wires the tree and dispatches.
"""

import argparse
from typing import Optional

from tex_tool.abstract import extract
from tex_tool.bib import entry_ops, merge_bib
from tex_tool.clean import comments
from tex_tool.ltex import combine_dict, new_command_to_setting


def build_parser() -> argparse.ArgumentParser:
    """Build the ``tex-tool`` argument parser with the whole subcommand tree."""
    parser = argparse.ArgumentParser(
        prog="tex-tool",
        description="Utilities for TeX, BibTeX, and LTeX.",
    )
    top = parser.add_subparsers(dest="group", required=True, metavar="GROUP")

    bib = top.add_parser("bib", help="BibTeX utilities")
    bib_sub = bib.add_subparsers(dest="command", required=True, metavar="COMMAND")
    merge_bib.add_subparser(bib_sub)
    entry_ops.add_subparser(bib_sub)

    dictionary = top.add_parser("dict", help="LTeX dictionary utilities")
    dict_sub = dictionary.add_subparsers(dest="command", required=True, metavar="COMMAND")
    combine_dict.add_subparser(dict_sub)
    new_command_to_setting.add_subparser(dict_sub)

    comments.add_subparser(top)
    extract.add_subparser(top)
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    """Parse *argv* (default: ``sys.argv``) and dispatch to the chosen subcommand."""
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        raise SystemExit(f"error: {exc}") from exc
