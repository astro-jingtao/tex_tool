"""Locate the agent skill shipped with this package.

The skill source lives at the repository root (``skills/`` beside ``src/``);
at build time it is copied into ``tex_tool/skills/`` so installed
distributions carry it. This module resolves that directory in both modes
and points at the packaged deployment guide (``skills/SKILL-DEPLOY.md``).
"""
import argparse
from pathlib import Path

COMMAND = "skills-path"
COMMAND_HELP = "Print the packaged agent-skill directory (deploy per its SKILL-DEPLOY.md)"


def skills_dir() -> Path:
    """Return the directory holding the skill tree.

    Installed distributions carry it under the ``tex_tool`` package; an
    editable checkout keeps it at the repository root beside ``src/``.
    """
    here = Path(__file__).resolve()
    candidates = (here.parent / "skills", here.parents[2] / "skills")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "packaged skills directory not found (looked in "
        f"{candidates[0]} and {candidates[1]})"
    )


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(COMMAND, help=COMMAND_HELP)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    directory = skills_dir()
    print(directory)
    print(f"Deploy per the guide at {directory / 'SKILL-DEPLOY.md'}")
