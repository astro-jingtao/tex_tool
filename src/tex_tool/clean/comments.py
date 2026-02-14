import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional


def remove_excessive_newlines(file_path: Path) -> None:
    """Collapse 3+ blank lines down to a single blank line."""
    try:
        content = file_path.read_text(encoding="utf-8")
        cleaned_content = re.sub(r"\n{3,}", "\n\n", content)
        cleaned_content = cleaned_content.strip() + "\n"
        file_path.write_text(cleaned_content, encoding="utf-8")
        print("Cleaned consecutive blank lines.")
    except Exception as exc:
        print(f"Warning: failed to clean blank lines: {exc}")


def clean_single_tex(
    input_path: str,
    output_path: Optional[str] = None,
    skip_newlines: bool = False,
) -> None:
    input_file = Path(input_path).resolve()

    if not input_file.exists() or input_file.suffix != ".tex":
        print(f"Error: file not found or invalid extension -> {input_path}")
        return

    if output_path:
        output_file = Path(output_path).resolve()
    else:
        output_file = input_file.parent / f"{input_file.stem}_cleaned.tex"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        to_clean_dir = tmp_path / "to_clean"
        to_clean_dir.mkdir()

        shutil.copy(input_file, to_clean_dir / input_file.name)
        print("Running arxiv_latex_cleaner...")
        try:
            subprocess.run(
                ["arxiv_latex_cleaner", str(to_clean_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            cleaned_tex = tmp_path / "to_clean_arXiv" / input_file.name

            if cleaned_tex.exists():
                shutil.copy(cleaned_tex, output_file)

                if not skip_newlines:
                    remove_excessive_newlines(output_file)

                print(f"Done. Saved to: {output_file}")
            else:
                print("Warning: cleaned file not found.")

        except subprocess.CalledProcessError as exc:
            print(f"Error: arxiv_latex_cleaner failed: {exc.stderr}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean a single LaTeX file.")
    parser.add_argument("input", help="Input .tex file")
    parser.add_argument("-o", "--output", help="Output filename")
    parser.add_argument(
        "--keep-newlines",
        action="store_true",
        help="Keep consecutive blank lines (default: collapse)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    clean_single_tex(args.input, args.output, skip_newlines=args.keep_newlines)


if __name__ == "__main__":
    main()
