from pathlib import Path

from tex_tool.clean.comments import remove_excessive_newlines


def test_remove_excessive_newlines(tmp_path: Path) -> None:
    target = tmp_path / "sample.tex"
    target.write_text("a\n\n\n\n\n b\n", encoding="utf-8")

    remove_excessive_newlines(target)

    cleaned = target.read_text(encoding="utf-8")
    assert cleaned == "a\n\n b\n"
