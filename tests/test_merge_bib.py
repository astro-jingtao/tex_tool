from tex_tool.bib.merge_bib import remove_duplicates


def test_remove_duplicates_same_id_same_doi():
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


def test_remove_duplicates_same_id_diff_doi():
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


def test_remove_duplicates_same_doi_removed_when_enabled():
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
