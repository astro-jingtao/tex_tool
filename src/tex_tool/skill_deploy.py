"""Locate the agent skill shipped with this package.

The skill tree lives inside the package at ``tex_tool/skills/`` — under
``site-packages`` in an installed distribution, at ``src/tex_tool/skills/``
in a checkout — so both modes resolve through this module's own location.
``python -m tex_tool.skills`` prints the same directory.
"""
import argparse
from pathlib import Path

COMMAND = "skills-path"
COMMAND_HELP = "Print the packaged agent-skill directory (deploy per its SKILL-DEPLOY.md)"


def skills_dir() -> Path:
    """Return the package's skills directory (checkout and installed alike)."""
    directory = Path(__file__).resolve().parent / "skills"
    if not directory.is_dir():
        raise FileNotFoundError(f"packaged skills directory not found (looked in {directory})")
    return directory


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(COMMAND, help=COMMAND_HELP)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    directory = skills_dir()
    print(directory)
    print(f"Deploy per the guide at {directory / 'SKILL-DEPLOY.md'}")
