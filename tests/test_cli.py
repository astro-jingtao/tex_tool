import pytest

from tex_tool.cli import build_parser


class TestTree:
    def test_every_command_parses(self, tmp_path) -> None:
        samples = [
            ["bib", "merge", "-f", str(tmp_path)],
            ["bib", "add", "refs.bib", "--file", "src.bib"],
            ["bib", "rename", "refs.bib", "a", "b"],
            ["bib", "search", "quasar"],
            ["clean", "main.tex"],
            ["dict", "merge", "a.txt", "b.txt"],
            ["dict", "new-command", "-i", "nc.tex"],
            ["abstract", "main.tex"],
        ]
        for argv in samples:
            args = build_parser().parse_args(argv)
            assert callable(args.func)

    def test_missing_group_errors(self) -> None:
        with pytest.raises(SystemExit):
            build_parser().parse_args([])

    def test_group_without_command_errors(self) -> None:
        with pytest.raises(SystemExit):
            build_parser().parse_args(["bib"])
