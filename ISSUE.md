# Known Issues

## bibtexparser is pinned to the v1 line (`>=1.4.0,<2`)

The code uses the bibtexparser v1 API — `bibtexparser.bparser.BibTexParser`, `bibtexparser.loads`, `bibtexparser.dump`, and `bibtexparser.bibdatabase.BibDatabase` in `src/tex_tool/bib/merge_bib.py`. bibtexparser 2.x removed that entire API surface (`bibtexparser.bparser` no longer exists), so any environment that resolves a 2.x release fails at call time with `AttributeError: module 'bibtexparser' has no attribute 'bparser'`. The dependency is therefore capped below 2 until the code migrates.

### Why v2 cannot be adopted yet

Every stable bibtexparser 2.x release published so far (2.0.0, 2.0.1, 2.1.0) declares `requires-python >= 3.10`. tex_tool supports Python 3.9+ (`requires-python = ">=3.9"` in `pyproject.toml`), and on 3.9 pip cannot install any v2 release at all — that interpreter always resolves to the 1.x line. Moving to the v2 API and raising the Python floor to 3.10 are one decision, not two: adopting v2 means dropping 3.9 support.

### Migration path, when that decision is made

1. Raise `requires-python` to `>= 3.10` and update the CI matrix floor accordingly (the 3.9 cell goes away).
2. Rewrite `parse_entries` and `write_entries` against the v2 API (the `bibtexparser.v2` module family), verifying that nonstandard entry types such as `@software` still parse — `parse_entries` deliberately passes `ignore_nonstandard_types=False` today, and that behavior must survive the migration.
3. Widen the pin in `pyproject.toml` to the `2.x` line and remove the v1 comment there.
