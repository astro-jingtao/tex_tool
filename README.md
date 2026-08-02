# tex_tool

A small collection of utilities for TeX, BibTeX, and LTeX workflows. The project is packaged as a Python module with command-line entry points.

## Modules and CLI

### BibTeX merge

- Module: `tex_tool.bib.merge_bib`
- CLI: `tex-tool-merge-bib`

This tool merges multiple `.bib` files, removes duplicates based on IDs, and optionally removes entries with identical DOIs. It also writes a human-readable report.

#### Core functions

- `read_entries(filename: str) -> List[Dict[str, str]]`
- `write_entries(entries: List[Dict[str, str]], filename: str)`
- `read_all_bibs(folder: str) -> List[Dict[str, str]]`
- `remove_duplicates(entries: List[Dict[str, str]], remove_same_doi: bool = False)`
- `get_doi_dict(entries_dict: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]`

#### CLI usage

```bash
tex-tool-merge-bib --folder files --output merged.bib --report report.txt
```

Options:

- `--folder`: folder containing `.bib` files
- `--output`: merged `.bib` output file
- `--report`: report output file
- `--remove-same-doi`: remove entries with duplicate DOIs

#### Flowchart of `remove_duplicates`

```mermaid
flowchart TD
    A[Start remove_duplicates] --> B[Iterate over entries]
    B --> C{ID exists?}
    C -- No --> D[Raise error]
    C -- Yes --> E{ID already in new_entries_dict?}
    E -- No --> F[Add entry to new_entries_dict]
    E -- Yes --> G{Same DOI?}
    G -- Yes --> I[Add to removed list]
    G -- No --> H[Generate new ID]
    H --> J[Add entry with new ID to new_entries_dict]
    I --> K[Continue]
    J --> K
    K --> L[End of entries?]
    L -- No --> B
    L -- Yes --> M[Check for same DOI entries]
    M --> N{Remove entries with same DOI?}
    N -- Yes --> O[Remove additional same DOI entries]
    N -- No --> P[Keep all same DOI entries]
    O --> Q[Finish and return results]
    P --> Q
```

### LaTeX cleaning

- Module: `tex_tool.clean.comments`
- CLI: `tex-tool-clean-comments`

This tool runs `arxiv_latex_cleaner` on a single `.tex` file and optionally collapses consecutive blank lines.

#### CLI usage

```bash
tex-tool-clean-comments path/to/main.tex -o main_cleaned.tex
```

Options:

- `-o`, `--output`: output file
- `--keep-newlines`: keep consecutive blank lines (default: collapse)

### Abstract extraction for arXiv

- Module: `tex_tool.abstract.extract`
- CLI: `tex-tool-extract-abstract`

This tool extracts the abstract from a `.tex` file and converts it to a plain-text format suitable for pasting into the arXiv submission system's abstract field. The pipeline:

1. Parses `\newcommand` / `\renewcommand` / `\providecommand` definitions from the preamble.
2. Extracts the `\begin{abstract}...\end{abstract}` block.
3. Strips LaTeX comments (`%...`).
4. Expands user-defined macros (iteratively to a fixed point — supports optional arguments with defaults, and is prefix-safe so `\bx` won't eat `\bxerr`).
5. Converts font/style commands outside math mode: `{\tt ...}` → `$\tt{...}$`, `{\rm ...}` → `$\rm{...}$`, `\textbf{...}` → `$\mathbf{...}$`, `\textcolor{...}{...}` → extract content, etc.
6. Wraps standalone LaTeX math commands (e.g. `\lesssim`, `\alpha`) that appear outside `$...$` in `$...$`.
7. Replaces special characters: `–` → `-`, `—` → `--`, `~` → space, ` ``...'' ` → `"..."`.
8. Collapses whitespace.

Citations (`\citet`, `\citep`, etc.) are left as-is. No hardcoded logic exists for specific macro names — every command is expanded only if defined in the preamble.

#### Core functions

- `find_abstract_block(content: str) -> Optional[str]`
- `clean_latex_comments(text: str) -> str`
- `extract_balanced_braces(s: str, start: int) -> Tuple[str, int]`
- `parse_newcommands(content: str) -> Dict[str, dict]`
- `expand_macros(text: str, definitions: Dict[str, dict]) -> str`
- `find_math_regions(text: str) -> List[Tuple[int, int]]`
- `wrap_standalone_math_commands(text: str, math_regions: List[...]) -> str`
- `convert_font_commands(text: str, math_regions: List[...]) -> str`
- `convert_special_chars(text: str) -> str`
- `extract_abstract_from_tex(tex_path: str) -> str`

#### CLI usage

```bash
tex-tool-extract-abstract main.tex
tex-tool-extract-abstract main.tex -o abstract.txt
```

### LTeX dictionary combine

- Module: `tex_tool.ltex.combine_dict`
- CLI: `tex-tool-combine-dict`

This tool merges two LTeX dictionary files into a combined output.

#### CLI usage

```bash
tex-tool-combine-dict dict1.txt dict2.txt --output dict_combine.txt
```

### LTeX new-command to settings

- Module: `tex_tool.ltex.new_command_to_setting`
- CLI: `tex-tool-new-command`

This tool converts `new_command.tex` definitions into a JSON settings file for LTeX.

#### CLI usage

```bash
tex-tool-new-command --input new_command.tex --output setting.json
```

## Installation

Local editable install for development:

```bash
pip install -e .
```

## Dependencies

- Python 3.8+
- `bibtexparser`
- `arxiv_latex_cleaner` (external CLI, required only for `tex-tool-clean-comments`)
- The abstract extraction module uses only the Python standard library — no extra dependencies.

## Tests

```bash
pytest
```
