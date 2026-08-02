from pathlib import Path

from tex_tool.bib.merge_bib import main, read_entries, remove_duplicates


def _write_bib(path: Path, entries: str) -> None:
    path.write_text(entries, encoding="utf-8")


class TestRemoveDuplicates:
    def test_same_id_same_doi(self) -> None:
        entries = [
            {"ID": "A1", "doi": "10.1/abc"},
            {"ID": "A1", "doi": "10.1/abc"},
        ]

        new_entries, removed, same_entry_diff_doi, same_doi_entries = remove_duplicates(
            entries
        )

        assert len(new_entries) == 1
        assert len(removed) == 1
        assert removed[0]["removed_reason"] == "same entry same doi"
        assert same_entry_diff_doi == []
        assert same_doi_entries == []

    def test_same_id_diff_doi(self) -> None:
        entries = [
            {"ID": "A1", "doi": "10.1/abc"},
            {"ID": "A1", "doi": "10.1/xyz"},
        ]

        new_entries, removed, same_entry_diff_doi, same_doi_entries = remove_duplicates(
            entries
        )

        assert len(new_entries) == 2
        assert len(removed) == 0
        assert len(same_entry_diff_doi) == 1
        assert same_entry_diff_doi[0]["ID"].startswith("A1_")
        assert same_doi_entries == []

    def test_same_doi_removed_when_enabled(self) -> None:
        entries = [
            {"ID": "A1", "doi": "10.1/abc"},
            {"ID": "B1", "doi": "10.1/abc"},
        ]

        new_entries, removed, same_entry_diff_doi, same_doi_entries = remove_duplicates(
            entries, remove_same_doi=True
        )

        assert len(new_entries) == 1
        assert len(removed) == 1
        assert removed[0]["removed_reason"] == "diff entry same doi"
        assert same_entry_diff_doi == []
        assert len(same_doi_entries) == 1


class TestCli:
    def test_writes_output_and_report(self, tmp_path: Path) -> None:
        folder = tmp_path / "bibs"
        folder.mkdir()
        output_file = tmp_path / "merged.bib"
        report_file = tmp_path / "report.txt"

        _write_bib(
            folder / "a.bib",
            "@article{A1, title={One}, doi={10.1/abc}}\n",
        )
        _write_bib(
            folder / "b.bib",
            "@article{A1, title={One}, doi={10.1/abc}}\n",
        )

        main([
            "--folder",
            str(folder),
            "--output",
            str(output_file),
            "--report",
            str(report_file),
        ])

        assert output_file.exists()
        assert report_file.exists()
        report_text = report_file.read_text(encoding="utf-8")
        assert "Merged entries:" in report_text


class TestReadEntries:
    def test_reads_software_entry(self, tmp_path: Path) -> None:
        bib_file = tmp_path / "software.bib"
        _write_bib(
            bib_file,
            (
                "@software{my_tool,\n"
                "  title = {My Tool},\n"
                "  author = {Doe, Jane},\n"
                "  version = {1.0.0},\n"
                "  url = {https://example.com/tool}\n"
                "}\n"
            ),
        )

        entries = read_entries(str(bib_file))

        assert len(entries) == 1
        assert entries[0]["ID"] == "my_tool"
        assert entries[0]["ENTRYTYPE"] == "software"
