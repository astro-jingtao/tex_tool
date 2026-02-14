from pathlib import Path

from tex_tool.clean.comments import main, remove_excessive_newlines


class TestComments:
    def test_remove_excessive_newlines(self, tmp_path: Path) -> None:
        target = tmp_path / "sample.tex"
        target.write_text("a\n\n\n\n\n b\n", encoding="utf-8")

        remove_excessive_newlines(target)

        cleaned = target.read_text(encoding="utf-8")
        assert cleaned == "a\n\n b\n"

    def test_cli_invalid_file(self, tmp_path: Path, capsys) -> None:
        invalid_path = tmp_path / "missing.tex"

        main([str(invalid_path)])

        captured = capsys.readouterr()
        assert "Error:" in captured.out
