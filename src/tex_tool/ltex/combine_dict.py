import argparse
from pathlib import Path
from typing import List, Optional


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def combine_dict_files(
    dict1_path: str,
    dict2_path: str,
    output_path: str,
) -> None:
    dict1 = read_lines(Path(dict1_path))
    dict2 = read_lines(Path(dict2_path))

    combined = list(set(dict1) | set(dict2))
    Path(output_path).write_text("".join(combined), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Combine two LTeX dictionary files.")
    parser.add_argument("dict1", help="First dictionary file")
    parser.add_argument("dict2", help="Second dictionary file")
    parser.add_argument("-o", "--output", default="dict_combine.txt", help="Output file")
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    combine_dict_files(args.dict1, args.dict2, args.output)


if __name__ == "__main__":
    main()
