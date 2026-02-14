import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_NEW_COMMAND_FILE = "./new_command.tex"
DEFAULT_SETTING_FILE = "./setting.json"


def is_empty_line(line: str) -> bool:
    return len(line.replace(" ", "").replace("\n", "")) == 0


def build_setting(lines: List[str]) -> Dict[str, str]:
    pattern = r"\{(.*?)\}"
    return {
        re.findall(pattern, line)[0]: "dummy"
        for line in lines
        if not is_empty_line(line)
    }


def convert_new_commands(new_command_file: str, setting_file: str) -> None:
    new_commands = Path(new_command_file).read_text(encoding="utf-8").splitlines()
    setting = build_setting(new_commands)
    with open(setting_file, "w", encoding="utf-8") as output_file:
        json.dump(setting, output_file, indent=4)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert new command definitions to LTeX settings JSON."
    )
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
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    convert_new_commands(args.input, args.output)


if __name__ == "__main__":
    main()
