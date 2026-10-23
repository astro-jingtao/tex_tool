r"""Convert ``\newcommand`` definitions from a .tex file into LTeX settings JSON.

Each command name is mapped to ``"dummy"``, the placeholder LTeX requires
for user-defined commands.
"""

import argparse
import json
from pathlib import Path
import re

DEFAULT_NEW_COMMAND_FILE = "./new_command.tex"
DEFAULT_SETTING_FILE = "./setting.json"

COMMAND = "new-command"
COMMAND_HELP = "Convert new command definitions to LTeX settings JSON"


def is_empty_line(line: str) -> bool:
    """Return *True* when *line* holds nothing but spaces and newlines."""
    return len(line.replace(" ", "").replace("\n", "")) == 0


def build_setting(lines: list[str]) -> dict[str, str]:
    r"""Map every ``\newcommand`` name in *lines* to the ``"dummy"`` placeholder."""
    pattern = r"\{(.*?)\}"
    return {re.findall(pattern, line)[0]: "dummy" for line in lines if not is_empty_line(line)}


def convert_new_commands(new_command_file: str, setting_file: str) -> None:
    r"""Read ``\newcommand`` lines from *new_command_file*; write the settings JSON."""
    new_commands = Path(new_command_file).read_text(encoding="utf-8").splitlines()
    setting = build_setting(new_commands)
    with open(setting_file, "w", encoding="utf-8") as output_file:
        json.dump(setting, output_file, indent=4)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the ``new-command`` subcommand on *subparsers*."""
    parser = subparsers.add_parser(COMMAND, help=COMMAND_HELP)
    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_NEW_COMMAND_FILE,
        help="Path to new_command.tex",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_SETTING_FILE,
        help="Output settings JSON",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Handle ``dict new-command``: convert the new-command file to settings JSON."""
    convert_new_commands(args.input, args.output)
