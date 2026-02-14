import json
from pathlib import Path

from tex_tool.ltex.new_command_to_setting import (
    build_setting,
    convert_new_commands,
    main,
)


class TestNewCommandToSetting:
    def test_build_setting_ignores_empty_lines(self) -> None:
        lines = ["\\newcommand{\\foo}{}", "", "   ", "\\newcommand{\\bar}{}"]
        setting = build_setting(lines)

        assert set(setting.keys()) == {"\\foo", "\\bar"}
        assert setting["\\foo"] == "dummy"

    def test_convert_new_commands_writes_json(self, tmp_path: Path) -> None:
        input_file = tmp_path / "new_command.tex"
        output_file = tmp_path / "setting.json"

        input_file.write_text("\\newcommand{\\foo}{}\n", encoding="utf-8")

        convert_new_commands(str(input_file), str(output_file))

        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data == {"\\foo": "dummy"}

    def test_cli(self, tmp_path: Path) -> None:
        input_file = tmp_path / "new_command.tex"
        output_file = tmp_path / "setting.json"

        input_file.write_text("\\newcommand{\\foo}{}\n", encoding="utf-8")

        main(["--input", str(input_file), "--output", str(output_file)])

        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data == {"\\foo": "dummy"}
