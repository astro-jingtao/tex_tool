import argparse
import os
from typing import Dict, List, Optional, Tuple

import bibtexparser

DEFAULT_REMOVE_SAME_DOI = False
DEFAULT_BIB_FOLDER = "files"
DEFAULT_REPORT = "report.txt"
DEFAULT_OUTPUT = "merged.bib"


def read_entries(filename: str) -> List[Dict[str, str]]:
    with open(filename, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    return bib_database.entries


def write_entries(entries: List[Dict[str, str]], filename: str) -> None:
    bib_database = bibtexparser.bibdatabase.BibDatabase()
    bib_database.entries = entries
    with open(filename, "w", encoding="utf-8") as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)


def read_all_bibs(folder: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for file in os.listdir(folder):
        if file.endswith(".bib"):
            entries += read_entries(os.path.join(folder, file))
    return entries


def remove_duplicates(
    entries: List[Dict[str, str]],
    remove_same_doi: bool = False,
) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[List[Dict[str, str]]]]:
    new_entries_dict: Dict[str, Dict[str, str]] = {}
    removed: List[Dict[str, str]] = []
    same_entry_diff_doi: List[Dict[str, str]] = []

    for entry in entries:
        if "ID" not in entry:
            raise ValueError("ID not found in entry")

        entry_id = entry["ID"]
        if entry_id not in new_entries_dict:
            new_entries_dict[entry_id] = entry.copy()
        elif (
            "doi" in entry
            and "doi" in new_entries_dict[entry_id]
            and entry["doi"] == new_entries_dict[entry_id]["doi"]
        ):
            removed_entry = entry.copy()
            removed_entry["removed_reason"] = "same entry same doi"
            removed.append(removed_entry)
        else:
            i = 1
            new_id = f"{entry_id}_{i}"
            while new_id in new_entries_dict:
                i += 1
                new_id = f"{entry_id}_{i}"
            new_entries_dict[new_id] = entry.copy()
            new_entries_dict[new_id]["ID"] = new_id
            same_entry_diff_doi.append(new_entries_dict[new_id])

    doi_dict = get_doi_dict(new_entries_dict)
    same_doi_entries: List[List[Dict[str, str]]] = []
    for ids in doi_dict.values():
        if len(ids) > 1:
            same_doi_entries.append([new_entries_dict[entry_id] for entry_id in ids])
            if remove_same_doi:
                for i in range(1, len(ids)):
                    removed_entry = new_entries_dict.pop(ids[i]).copy()
                    removed_entry["removed_reason"] = "diff entry same doi"
                    removed.append(removed_entry)

    return new_entries_dict, removed, same_entry_diff_doi, same_doi_entries


def get_doi_dict(entries_dict: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    doi_dict: Dict[str, List[str]] = {}
    for entry_id, this_entry in entries_dict.items():
        if "doi" in this_entry:
            doi = this_entry["doi"]
            doi_dict.setdefault(doi, []).append(entry_id)
    return doi_dict


def write_report(
    report_path: str,
    total_entries: int,
    merged_entries: int,
    removed: List[Dict[str, str]],
    same_entry_diff_doi: List[Dict[str, str]],
    same_doi_entries: List[List[Dict[str, str]]],
    remove_same_doi: bool,
) -> None:
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(f"Total entries: {total_entries}\n")
        report_file.write(f"Merged entries: {merged_entries}\n")
        report_file.write(f"Removed entries: {len(removed)}\n")

        if remove_same_doi:
            report_file.write(
                f"Different entry same doi: {len(same_doi_entries)} (removed)\n"
            )
        else:
            report_file.write(
                f"Different entry same doi: {len(same_doi_entries)} (only reported)\n"
            )

        report_file.write(
            f"Same entry different doi: {len(same_entry_diff_doi)} (only reported)\n"
        )
        report_file.write("\n")
        report_file.write("--------------- details ---------------\n\n")

        report_file.write("Removed entries:\n")
        for entry in removed:
            report_file.write(f"{entry['ID']}:\n")
            report_file.write(f"    Removed reason: {entry['removed_reason']}\n")
            report_file.write(
                f"    DOI: {entry.get('doi', 'None')}\n"
            )

        report_file.write("\nDifferent entry same doi:\n")
        for entries in same_doi_entries:
            report_file.write(f"Same doi: {entries[0]['doi']}\n")
            for entry in entries:
                report_file.write(f"    {entry['ID']}\n")
                report_file.write(f"        DOI: {entry['doi']}\n")
            report_file.write("\n")

        report_file.write("\nSame entry different doi:\n")
        for entry in same_entry_diff_doi:
            report_file.write(f"{entry['ID']}:\n")
            report_file.write(
                f"    DOI: {entry.get('doi', 'None')}\n"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge BibTeX files with de-duplication.")
    parser.add_argument(
        "-f",
        "--folder",
        default=DEFAULT_BIB_FOLDER,
        help="Folder containing .bib files",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output .bib filename",
    )
    parser.add_argument(
        "-r",
        "--report",
        default=DEFAULT_REPORT,
        help="Report output filename",
    )
    parser.add_argument(
        "--remove-same-doi",
        action="store_true",
        default=DEFAULT_REMOVE_SAME_DOI,
        help="Remove entries with the same DOI",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    entries = read_all_bibs(args.folder)
    (
        new_entries_dict,
        removed,
        same_entry_diff_doi,
        same_doi_entries,
    ) = remove_duplicates(entries, remove_same_doi=args.remove_same_doi)

    write_entries(list(new_entries_dict.values()), args.output)
    write_report(
        report_path=args.report,
        total_entries=len(entries),
        merged_entries=len(new_entries_dict),
        removed=removed,
        same_entry_diff_doi=same_entry_diff_doi,
        same_doi_entries=same_doi_entries,
        remove_same_doi=args.remove_same_doi,
    )


if __name__ == "__main__":
    main()
