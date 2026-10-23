from pathlib import Path

import pytest

from tex_tool.bib import entry_ops
from tex_tool.bib.entry_ops import add_entries, rename_entry, search_entries
from tex_tool.bib.merge_bib import read_entries
from tex_tool.cli import main


def _write_bib(path: Path, entries: str) -> None:
    path.write_text(entries, encoding="utf-8")


EXISTING = (
    "@article{A1,\n  title = {Alpha Paper},\n  author = {Doe, Jane},\n  doi = {10.1/abc}\n}\n"
)
INCOMING = "@article{B2,\n  title = {Beta Paper},\n  author = {Roe, Richard},\n  year = {2024}\n}\n"


class TestAdd:
    def test_appends_entry(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        added = add_entries(str(bib), INCOMING)

        assert added == ["B2"]
        assert len(read_entries(str(bib))) == 2

    def test_creates_missing_file(self, tmp_path: Path) -> None:
        bib = tmp_path / "new.bib"

        added = add_entries(str(bib), INCOMING)

        assert added == ["B2"]
        assert bib.exists()

    def test_rejects_duplicate_key_and_keeps_file(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        with pytest.raises(ValueError, match="A1"):
            add_entries(str(bib), EXISTING)

        assert bib.read_text(encoding="utf-8") == EXISTING

    def test_rejects_duplicate_inside_batch(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"

        with pytest.raises(ValueError, match="batch"):
            add_entries(str(bib), EXISTING + EXISTING)

        assert not bib.exists()

    def test_rename_before_add(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        add_entries(str(bib), INCOMING, rename="jing2024")

        ids = [entry["ID"] for entry in read_entries(str(bib))]
        assert ids == ["A1", "jing2024"]

    def test_rename_needs_single_entry(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"

        with pytest.raises(ValueError, match="exactly one"):
            add_entries(str(bib), EXISTING + INCOMING, rename="x")


class TestRename:
    def test_renames_in_place(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        rename_entry(str(bib), "A1", "doe2024")

        text = bib.read_text(encoding="utf-8")
        assert "doe2024" in text
        assert "{A1," not in text
        assert read_entries(str(bib))[0]["ID"] == "doe2024"

    def test_missing_old_key(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        with pytest.raises(ValueError, match="not found"):
            rename_entry(str(bib), "missing", "x")

    def test_new_key_already_exists(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING + INCOMING)

        with pytest.raises(ValueError, match="already exists"):
            rename_entry(str(bib), "B2", "A1")

    def test_new_equals_old(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        with pytest.raises(ValueError, match="equals"):
            rename_entry(str(bib), "A1", "A1")


class TestSearch:
    def _make_bib(self, tmp_path: Path) -> Path:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING + INCOMING + "@misc{note1,\n  title = {My Notes}\n}\n")
        return bib

    def test_all_fields_by_default(self, tmp_path: Path) -> None:
        bib = self._make_bib(tmp_path)
        matches = search_entries([str(bib)], "10.1")
        assert [entry["ID"] for entry in matches] == ["A1"]

    def test_field_title(self, tmp_path: Path) -> None:
        bib = self._make_bib(tmp_path)
        matches = search_entries([str(bib)], "beta", field="title")
        assert [entry["ID"] for entry in matches] == ["B2"]

    def test_field_key_matches_entry_key(self, tmp_path: Path) -> None:
        bib = self._make_bib(tmp_path)
        matches = search_entries([str(bib)], "note", field="key")
        assert [entry["ID"] for entry in matches] == ["note1"]

    def test_field_missing_on_entry_is_skipped(self, tmp_path: Path) -> None:
        bib = self._make_bib(tmp_path)
        matches = search_entries([str(bib)], "2024", field="year")
        assert [entry["ID"] for entry in matches] == ["B2"]

    def test_no_match_returns_empty(self, tmp_path: Path) -> None:
        bib = self._make_bib(tmp_path)
        assert search_entries([str(bib)], "gamma") == []


class TestAddCli:
    def test_add_from_local_file(self, tmp_path: Path, capsys) -> None:
        target = tmp_path / "refs.bib"
        _write_bib(target, EXISTING)
        source = tmp_path / "src.bib"
        _write_bib(source, INCOMING)

        main(["bib", "add", str(target), "--file", str(source)])

        assert len(read_entries(str(target))) == 2
        assert "Added 1 entry" in capsys.readouterr().out

    def test_add_from_scix_mocked(self, tmp_path: Path, monkeypatch) -> None:
        target = tmp_path / "refs.bib"
        _write_bib(target, EXISTING)
        calls = {}

        def fake_export_bibtex(bibcode, token, base_url=...):
            calls["bibcode"] = bibcode
            calls["token"] = token
            return INCOMING

        monkeypatch.setattr(entry_ops, "export_bibtex", fake_export_bibtex)

        main(
            [
                "bib",
                "add",
                str(target),
                "--scix",
                "2024ApJS..272...24C",
                "--token",
                "tok",
                "--rename",
                "jing2024",
            ]
        )

        assert calls["bibcode"] == "2024ApJS..272...24C"
        assert calls["token"] == "tok"
        ids = [entry["ID"] for entry in read_entries(str(target))]
        assert ids == ["A1", "jing2024"]

    def test_add_scix_without_token_fails(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.delenv("SCIX_TOKEN", raising=False)
        target = tmp_path / "refs.bib"
        _write_bib(target, EXISTING)

        with pytest.raises(SystemExit, match="token"):
            main(["bib", "add", str(target), "--scix", "2024X"])


class TestRenameSearchCli:
    def test_rename(self, tmp_path: Path) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING)

        main(["bib", "rename", str(bib), "A1", "doe2024"])

        assert read_entries(str(bib))[0]["ID"] == "doe2024"

    def test_search_prints_matches(self, tmp_path: Path, capsys) -> None:
        bib = tmp_path / "refs.bib"
        _write_bib(bib, EXISTING + INCOMING)

        main(["bib", "search", "beta", str(bib), "--field", "title"])

        out = capsys.readouterr().out
        assert "Beta Paper" in out
        assert "Alpha Paper" not in out
