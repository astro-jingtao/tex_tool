from pathlib import Path

from tex_tool.ltex.combine_dict import combine_dict_files


def test_combine_dict_files(tmp_path: Path) -> None:
    dict1 = tmp_path / "dict1.txt"
    dict2 = tmp_path / "dict2.txt"
    output = tmp_path / "out.txt"

    dict1.write_text("alpha\nbeta\n", encoding="utf-8")
    dict2.write_text("beta\ngamma\n", encoding="utf-8")

    combine_dict_files(str(dict1), str(dict2), str(output))

    combined = output.read_text(encoding="utf-8").splitlines()
    assert set(combined) == {"alpha", "beta", "gamma"}
