import os
from typing import Dict, List

import bibtexparser

# SETTINGS
REMOVE_SAME_DOI = False
BIB_FOLD = 'files'
REPORT = 'report.txt'
OUTPUT = 'merged.bib'

def read_entries(filename):
    with open(filename, encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    return bib_database.entries


def write_entries(entries: List, filename):
    bib_database = bibtexparser.bibdatabase.BibDatabase()
    bib_database.entries = entries
    with open(filename, 'w', encoding='utf-8') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)


def read_all_bibs(fold):
    entries = []
    for file in os.listdir(fold):
        if file.endswith(".bib"):
            entries += read_entries(os.path.join(fold, file))
    return entries


def remove_duplicates(entries: List[Dict[str, str]], remove_same_doi=False):
    new_entries_dict: Dict[str, Dict[str, str]] = {}
    removed = []
    same_entry_diff_doi = []
    for entry in entries:
        if 'ID' not in entry:
            raise ValueError("ID not found in entry")

        entry_id = entry['ID']
        if entry_id not in new_entries_dict:
            new_entries_dict[entry_id] = entry.copy()
        elif 'doi' in entry and 'doi' in new_entries_dict[entry_id] and entry[
                'doi'] == new_entries_dict[entry_id]['doi']:
            removed_entry = entry.copy()
            removed_entry['removed_reason'] = 'same entry same doi'
            removed.append(removed_entry)
        else:
            i = 1
            new_id = f"{entry_id}_{i}"
            while new_id in new_entries_dict:
                i += 1
                new_id = f"{entry_id}_{i}"
            new_entries_dict[new_id] = entry.copy()
            new_entries_dict[new_id]['ID'] = new_id
            same_entry_diff_doi.append(new_entries_dict[new_id])

    doi_dict = get_doi_dict(new_entries_dict)
    same_doi_entries = []
    for ids in doi_dict.values():
        if len(ids) > 1:
            same_doi_entries.append([new_entries_dict[id] for id in ids])
            if remove_same_doi:
                for i in range(1, len(ids)):
                    removed_entry = new_entries_dict.pop(ids[i]).copy()
                    removed_entry['removed_reason'] = 'diff entry same doi'
                    removed.append(removed_entry)

    return new_entries_dict, removed, same_entry_diff_doi, same_doi_entries


def get_doi_dict(entries_dict: Dict[str, Dict[str, str]]):
    doi_dict = {}
    for _id, this_entry in entries_dict.items():
        if 'doi' in this_entry:
            if this_entry['doi'] not in doi_dict:
                doi_dict[this_entry['doi']] = [_id]
            else:
                doi_dict[this_entry['doi']].append(_id)
    return doi_dict


def main():
    entries = read_all_bibs(BIB_FOLD)
    new_entries_dict, removed, same_entry_diff_doi, same_doi_entries = remove_duplicates(
        entries, remove_same_doi=REMOVE_SAME_DOI)
    write_entries(list(new_entries_dict.values()), OUTPUT)

    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write(f"Total entries: {len(entries)}\n")
        f.write(f"Merged entries: {len(new_entries_dict)}\n")
        f.write(f"Removed entries: {len(removed)}\n")

        if REMOVE_SAME_DOI:
            f.write(f"Different entry same doi: {len(same_doi_entries)} (removed)\n")
        else:
            f.write(f"Different entry same doi: {len(same_doi_entries)} (only reported)\n")

        f.write(f"Same entry different doi: {len(same_entry_diff_doi)}  (only reported)\n")
        f.write("\n")
        f.write("--------------- details ---------------\n")
        f.write("\n")
        f.write("Removed entries:\n")
        for entry in removed:
            # ID, removed_reason, doi
            f.write(f"{entry['ID']}:\n")
            f.write(f"    Removed reason: {entry['removed_reason']}\n")
            if 'doi' in entry:
                f.write(f"    DOI: {entry['doi']}\n")
            else:
                f.write("    DOI: None\n")

        f.write("\n")
        f.write("Different entry same doi:\n")
        for entries in same_doi_entries:
            # ID, doi
            f.write(f"Same doi: {entries[0]['doi']}\n")
            for entry in entries:
                f.write(f"    {entry['ID']}\n")
                f.write(f"        DOI: {entry['doi']}\n")
            f.write("\n")

        f.write("\n")
        f.write("Same entry different doi:\n")
        for entry in same_entry_diff_doi:
            # ID, doi
            f.write(f"{entry['ID']}:\n")
            if 'doi' in entry:
                f.write(f"    DOI: {entry['doi']}\n")
            else:
                f.write("    DOI: None\n")


if __name__ == '__main__':
    main()
